import os
import re
from typing import Dict, List, Optional
import yaml

from dsl.dsl_parser import DslParser, ChatFlow
from dsl.interpreter import Interpreter
from core.action_executor import ActionExecutor
from core.session_manager import SessionManager, Session

class Chatbot:
    """
    The main orchestrator for the chatbot. It loads all flows, manages sessions,
    and routes user input to the appropriate interpreter.

    支持混合模式：规则优先 + LLM语义理解兜底
    """
    def __init__(self, flows_dir: str = "dsl/flows", llm_responder=None):
        self.flows: Dict[str, ChatFlow] = self._load_flows(flows_dir)
        self.llm_responder = llm_responder  # 可选的LLM响应器

        # 创建解释器时传入LLM响应器
        self.interpreters: Dict[str, Interpreter] = {
            name: Interpreter(flow, llm_responder=llm_responder)
            for name, flow in self.flows.items()
        }
        self.session_manager = SessionManager()
        self.action_executor = ActionExecutor()

        # 构建流程意图映射（用于LLM匹配）
        self.flow_intents = self._build_flow_intent_map()

        print(f"Chatbot initialized with {len(self.flows)} flows.")
        if llm_responder:
            print(f"  [LLM] LLM响应器已启用（混合模式）")
        else:
            print(f"  [INFO] 仅使用规则匹配（无LLM）")

    def _build_flow_intent_map(self) -> Dict[str, str]:
        """
        构建流程到意图的映射，用于LLM匹配

        Returns:
            {flow_name: intent_description}
        """
        default_intents = {
            "售前产品咨询流程": "用户想了解产品信息、查看商品详情、询问价格和功能",
            "售中订单管理流程": "用户想查询订单状态、查看物流信息、取消订单",
            "标准退款流程": "用户想申请退款或退货、反馈商品质量问题",
            "发票服务流程": "用户需要开具发票、提供发票抬头和税号",
            "耳机故障排查流程": "用户反馈耳机故障、设备连接问题、需要技术支持",
            "通用闲聊流程": "用户打招呼、闲聊、问候"
        }

        intent_map = {}
        for flow_name in self.flows.keys():
            intent_map[flow_name] = default_intents.get(flow_name, f"与{flow_name}相关的咨询")

        return intent_map

    def _load_flows(self, flows_dir: str) -> Dict[str, ChatFlow]:
        """Loads all DSL flow files from a directory."""
        flows = {}
        if not os.path.exists(flows_dir):
            print(f"Warning: Flows directory not found at '{flows_dir}'")
            return flows

        for root, _, files in os.walk(flows_dir):
            for filename in files:
                if filename.endswith(".yaml"):
                    file_path = os.path.join(root, filename)
                    parser = DslParser(file_path)
                    flow = parser.get_flow()
                    if flow:
                        flows[flow.name] = flow
                        print(f"  - Loaded flow: '{flow.name}' from {filename}")
        return flows

    def _try_rule_based_trigger(self, user_input: str) -> Optional[str]:
        """
        尝试使用规则匹配触发流程（优先级最高）

        Args:
            user_input: 用户输入

        Returns:
            匹配的流程名称，如果未匹配则返回None
        """
        print(f"[步骤1: 规则匹配] 检查用户输入: '{user_input}'")

        for flow_name, flow in self.flows.items():
            entry_state = flow.get_entry_state()
            if entry_state:
                for trigger in entry_state.get("triggers", []):
                    if trigger.get("type") == "regex":
                        pattern = trigger.get("value", "")
                        if re.search(pattern, user_input, re.IGNORECASE):
                            print(f"  [OK] [规则匹配成功] 触发流程: '{flow_name}' (regex: '{pattern}')")
                            return flow_name

        print(f"  [FAIL] [规则匹配失败] 未匹配到任何流程")
        return None

    def _try_llm_based_trigger(self, user_input: str) -> Optional[str]:
        """
        使用LLM进行意图识别，触发流程（兜底方案）

        Args:
            user_input: 用户输入

        Returns:
            匹配的流程名称，如果未匹配则返回None
        """
        if not self.llm_responder:
            print(f"  [SKIP] [LLM匹配跳过] LLM响应器未配置")
            return None

        print(f"[步骤2: LLM语义匹配] 调用LLM分析意图...")

        try:
            # 准备可用的意图列表
            available_intents = list(self.flow_intents.values())

            result = self.llm_responder.recognize_intent(
                user_input=user_input,
                available_intents=available_intents
            )

            intent = result.get("intent", "")
            confidence = result.get("confidence", 0.0)
            reasoning = result.get("reasoning", "")

            print(f"  LLM识别结果: 意图='{intent}', 置信度={confidence:.2f}")
            print(f"  理由: {reasoning}")

            # 置信度阈值：>=0.7才认为匹配
            if confidence < 0.7:
                print(f"  [FAIL] [LLM匹配失败] 置信度过低 ({confidence:.2f} < 0.7)")
                return None

            # 根据意图找到对应的流程
            for flow_name, flow_intent in self.flow_intents.items():
                # 模糊匹配：检查识别出的意图是否包含在流程意图描述中
                if intent in flow_intent or any(keyword in user_input for keyword in intent.split()):
                    print(f"  [OK] [LLM匹配成功] 触发流程: '{flow_name}'")
                    return flow_name

            print(f"  [FAIL] [LLM匹配失败] 意图'{intent}'未映射到任何流程")
            return None

        except Exception as e:
            print(f"  [ERROR] [LLM匹配异常] {type(e).__name__}: {str(e)}")
            return None

    def handle_message(self, session_id: str, user_input: str, user_id: Optional[str] = None) -> List[str]:
        """
        Handles a user's message, routes it to the correct flow, and returns the bot's responses.

        Args:
            session_id: 会话ID
            user_input: 用户输入
            user_id: 用户ID（可选，用于识别用户并进行个性化查询）

        处理流程（全局流程切换机制）：
        1. 无论是否在某个流程中，都尝试匹配新流程（规则优先 + LLM兜底）
        2. 如果匹配到新流程：
           a) 如果与当前流程不同，立即切换到新流程
           b) 如果与当前流程相同，继续执行当前流程
        3. 如果未匹配到新流程但有活跃流程，继续执行当前流程
        4. 如果既没有匹配也没有活跃流程，返回默认提示

        这种设计允许用户随时通过关键词切换到其他业务流程，解决了"通用闲聊流程死锁"问题。
        """
        session = self.session_manager.get_session(session_id, user_id)
        session.last_user_input = user_input

        active_flow_name = session.get("active_flow_name")

        # ==================== 全局流程切换机制 ====================
        # 【核心改进】无论当前是否在某个流程中，都尝试匹配新流程
        # 这解决了"通用闲聊流程死锁"问题，允许用户随时切换到其他业务流程

        print(f"\n{'='*70}")
        print(f"[流程匹配] 用户输入: '{user_input}'")
        if active_flow_name:
            print(f"[当前流程] {active_flow_name}")
        print(f"{'='*70}")

        # Step 1: 优先尝试规则匹配（全局）
        matched_flow_name = self._try_rule_based_trigger(user_input)

        # Step 2: 规则匹配失败，尝试LLM语义理解（兜底）
        if not matched_flow_name:
            matched_flow_name = self._try_llm_based_trigger(user_input)

        # Step 3: 处理流程切换逻辑
        if matched_flow_name:
            # 检查是否需要切换流程
            if matched_flow_name != active_flow_name:
                # 流程切换：从当前流程切换到新流程
                if active_flow_name:
                    print(f"[流程切换] 从 '{active_flow_name}' 切换到 '{matched_flow_name}'")
                else:
                    print(f"[流程启动] 启动流程: '{matched_flow_name}'")

                session.set("active_flow_name", matched_flow_name)
                interpreter = self.interpreters[matched_flow_name]
                flow = self.flows[matched_flow_name]
                # 获取新流程的初始动作
                actions = interpreter.get_initial_actions()
                session.current_state_id = flow.entry_point
            else:
                # 相同流程：继续当前流程
                print(f"[流程继续] 继续流程: '{active_flow_name}'")
                interpreter = self.interpreters[active_flow_name]
                actions = interpreter.process(session, user_input)

                # 检查流程是否结束
                next_state = self.flows[active_flow_name].get_state(session.current_state_id)
                if "end" in session.current_state_id and not next_state.get("actions"):
                    session.set("active_flow_name", None)
                    print(f"[流程结束] 流程'{active_flow_name}'已结束")

        elif active_flow_name:
            # 没有匹配到新流程，但有活跃流程：继续当前流程
            print(f"[流程继续] 未匹配到新流程，继续当前流程: '{active_flow_name}'")
            interpreter = self.interpreters[active_flow_name]
            actions = interpreter.process(session, user_input)

            # 检查流程是否结束
            next_state = self.flows[active_flow_name].get_state(session.current_state_id)
            if "end" in session.current_state_id and not next_state.get("actions"):
                session.set("active_flow_name", None)
                print(f"[流程结束] 流程'{active_flow_name}'已结束")

        else:
            # 既没有匹配到新流程，也没有活跃流程
            print(f"[流程匹配失败] 无法理解用户意图")
            actions = []

        print(f"{'='*70}\n")

        # 如果没有任何动作，返回默认提示
        if not actions:
            return ["抱歉，我暂时无法理解您的意思。您可以尝试：\n- 咨询产品信息\n- 查询订单状态\n- 申请退款退货\n- 开具发票\n- 反馈故障问题"]

        # 执行动作
        responses = self.action_executor.execute(actions, session)
        return responses
