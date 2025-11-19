from typing import List, Dict, Any, Optional
import re
from dsl.dsl_parser import DslParser, ChatFlow
from core.session_manager import Session

class Interpreter:
    def __init__(self, chat_flow: ChatFlow, llm_responder=None):
        if not isinstance(chat_flow, ChatFlow):
            raise TypeError("chat_flow must be an instance of ChatFlow")
        self.chat_flow = chat_flow
        self.llm_responder = llm_responder  # 可选的LLM响应器，用于语义理解

    def process(self, session: Session, user_input: str) -> List[Dict[str, Any]]:
        """
        处理用户输入，并根据当前状态和转换规则决定下一步的动作。
        """
        # 如果 session 没有当前状态 (比如是新 session)，则从流程入口点开始
        if not session.current_state_id:
            session.current_state_id = self.chat_flow.entry_point

        current_state_id = session.current_state_id
        current_state = self.chat_flow.get_state(current_state_id)
        if not current_state:
            return [{"type": "respond", "text": f"错误：找不到状态 {current_state_id}。"}]

        print(f"[Interpreter] 当前状态: {current_state_id}")

        # 寻找匹配的转换规则
        transitions = current_state.get("transitions", [])
        print(f"[Interpreter] 检查 {len(transitions)} 个转换规则")

        matched_transition = None
        for i, transition in enumerate(transitions):
            condition = transition.get("condition")
            print(f"[Interpreter] 检查转换 #{i+1}, condition={condition is not None}")
            if self._is_condition_met(condition, user_input, session):
                matched_transition = transition
                print(f"[Interpreter] ✓ 转换 #{i+1} 匹配成功, target={transition.get('target')}")
                break
            else:
                print(f"[Interpreter] ✗ 转换 #{i+1} 不匹配")

        # 如果没有匹配的条件，且存在一个没有条件的"兜底"转换
        if not matched_transition:
            print(f"[Interpreter] 未找到条件匹配，查找兜底转换...")
            for i, transition in enumerate(transitions):
                if "condition" not in transition:
                    matched_transition = transition
                    print(f"[Interpreter] ✓ 找到兜底转换 #{i+1}, target={transition.get('target')}")
                    break

        if matched_transition:
            # 转换状态
            next_state_id = matched_transition.get("target")
            print(f"[Interpreter] 状态转换: {current_state_id} -> {next_state_id}")
            session.current_state_id = next_state_id
            next_state = self.chat_flow.get_state(next_state_id)
            if next_state:
                actions = next_state.get("actions", [])
                print(f"[Interpreter] 返回 {len(actions)} 个动作")
                return actions
            else:
                return [{"type": "respond", "text": f"错误：找不到目标状态 {next_state_id}。"}]

        # 如果没有找到任何匹配的转换
        print(f"[Interpreter] 警告：没有找到任何匹配的转换，返回默认响应")
        return [{"type": "respond", "text": "抱歉，我不知道如何回应。"}]

    def _is_condition_met(self, condition: Optional[Dict[str, Any]], user_input: str, session: Session = None) -> bool:
        """
        检查条件是否满足

        支持的条件类型：
        1. all: 所有子条件都必须满足
        2. any: 任一子条件满足即可
        3. regex: 正则表达式匹配
        4. variable_equals: 会话变量值比较

        Args:
            condition: 条件字典
            user_input: 用户输入
            session: 会话对象（用于变量比较）

        Returns:
            True表示条件满足，False表示不满足
        """
        if condition is None:
            return False

        # 支持 all 逻辑：所有条件都必须满足
        if "all" in condition:
            rules = condition["all"]
            for rule in rules:
                if not self._check_single_rule(rule, user_input, session):
                    return False
            return True

        # 支持 any 逻辑：任一条件满足即可
        if "any" in condition:
            rules = condition["any"]
            for rule in rules:
                if self._check_single_rule(rule, user_input, session):
                    return True
            return False

        # 单个规则（向后兼容）
        return self._check_single_rule(condition, user_input, session)

    def _check_single_rule(self, rule: Dict[str, Any], user_input: str, session: Session = None) -> bool:
        """
        检查单个规则是否满足

        Args:
            rule: 规则字典
            user_input: 用户输入
            session: 会话对象

        Returns:
            True表示规则满足，False表示不满足
        """
        rule_type = rule.get("type")

        # 正则表达式匹配（规则优先）
        if rule_type == "regex":
            pattern = rule.get("value", "")
            matched = bool(re.search(pattern, user_input, re.IGNORECASE))
            if matched:
                print(f"  ✓ [规则匹配] regex: '{pattern}' 匹配成功")
            return matched

        # 变量值比较
        elif rule_type == "variable_equals":
            var_name = rule.get("variable")
            expected_value = rule.get("value")

            if session is None or var_name is None:
                return False

            # 获取会话变量值
            actual_value = session.variables.get(var_name)

            # 比较值
            return actual_value == expected_value

        # 变量存在性检查
        elif rule_type == "variable_exists":
            var_name = rule.get("variable")
            if session is None or var_name is None:
                return False
            return var_name in session.variables

        # LLM语义匹配（新增）
        elif rule_type == "llm_semantic":
            if not self.llm_responder:
                print(f"  ✗ [LLM语义匹配] LLM响应器未配置，跳过")
                return False

            semantic_meaning = rule.get("semantic_meaning", "")
            confidence_threshold = rule.get("confidence_threshold", 0.7)

            # 准备会话上下文
            session_context = None
            if session:
                session_context = {
                    "current_state_id": session.current_state_id,
                    "variables": session.variables
                }

            try:
                result = self.llm_responder.check_semantic_match(
                    user_input=user_input,
                    semantic_meaning=semantic_meaning,
                    session_context=session_context
                )

                matched = result.get("matched", False) and result.get("confidence", 0.0) >= confidence_threshold
                if matched:
                    print(f"  ✓ [LLM语义匹配] 成功，置信度: {result.get('confidence', 0):.2f}, 理由: {result.get('reasoning', '')}")
                else:
                    print(f"  ✗ [LLM语义匹配] 失败，置信度: {result.get('confidence', 0):.2f}")

                return matched

            except Exception as e:
                print(f"  ✗ [LLM语义匹配] 异常: {str(e)}")
                return False

        # 未知规则类型
        print(f"  ✗ [规则检查] 未知规则类型: {rule_type}")
        return False
    
    def get_initial_actions(self) -> List[Dict[str, Any]]:
        """获取流程入口状态的动作"""
        entry_state = self.chat_flow.get_entry_state()
        if entry_state:
            return entry_state.get("actions", [])
        return []


if __name__ == '__main__':
    from core.action_executor import ActionExecutor
    from core.session_manager import SessionManager

    parser = DslParser('dsl/examples/refund_flow.v2.yaml')
    chat_flow = parser.get_flow()

    if not chat_flow:
        exit()

    # 初始化核心组件
    interpreter = Interpreter(chat_flow)
    action_executor = ActionExecutor()
    session_manager = SessionManager()
    
    # 创建一个新的对话 session
    session = session_manager.create_session()
    print(f"--- 新对话开始 (Session ID: {session.session_id}) ---")
    
    # 打印初始状态的响应
    initial_actions = interpreter.get_initial_actions()
    # 在执行动作前，需要设置当前状态
    session.current_state_id = chat_flow.entry_point
    responses = action_executor.execute(initial_actions, session)
    for res in responses:
        print(f"机器人: {res}")

    # 模拟多轮对话
    test_inputs = [
        "你好，我想退货，因为收到的商品坏掉了。",
        "我的订单号是 A1234567890",
        "是的"
    ]

    for user_input in test_inputs:
        print(f"\n用户: {user_input}")
        
        session.last_user_input = user_input
        
        actions = interpreter.process(session, user_input)
        
        responses = action_executor.execute(actions, session)
        for res in responses:
            print(f"机器人: {res}")
        
        print(f"(当前状态: {session.current_state_id})")

    print("\n--- 对话结束 ---")
