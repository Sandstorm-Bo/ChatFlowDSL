from typing import List, Dict, Any, Optional
import re
from dsl.dsl_parser import DslParser, ChatFlow
from core.session_manager import Session

class Interpreter:
    def __init__(self, chat_flow: ChatFlow):
        if not isinstance(chat_flow, ChatFlow):
            raise TypeError("chat_flow must be an instance of ChatFlow")
        self.chat_flow = chat_flow

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

        # 寻找匹配的转换规则
        transitions = current_state.get("transitions", [])
        matched_transition = None
        for transition in transitions:
            condition = transition.get("condition")
            if self._is_condition_met(condition, user_input):
                matched_transition = transition
                break
        
        # 如果没有匹配的条件，且存在一个没有条件的“兜底”转换
        if not matched_transition:
            for transition in transitions:
                if "condition" not in transition:
                    matched_transition = transition
                    break

        if matched_transition:
            # 转换状态
            next_state_id = matched_transition.get("target")
            session.current_state_id = next_state_id
            next_state = self.chat_flow.get_state(next_state_id)
            if next_state:
                return next_state.get("actions", [])
            else:
                return [{"type": "respond", "text": f"错误：找不到目标状态 {next_state_id}。"}]

        # 如果没有找到任何匹配的转换
        return [{"type": "respond", "text": "抱歉，我不知道如何回应。"}]

    def _is_condition_met(self, condition: Optional[Dict[str, Any]], user_input: str) -> bool:
        """检查单个条件是否满足。目前只支持简单的正则匹配。"""
        if condition is None:
            return False

        if "all" in condition:
            rules = condition["all"]
            for rule in rules:
                if rule.get("type") == "regex":
                    if not re.search(rule.get("value", ""), user_input):
                        return False
            return True

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
    responses = action_executor.execute(initial_actions, session.to_dict())
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
        
        responses = action_executor.execute(actions, session.to_dict())
        for res in responses:
            print(f"机器人: {res}")
        
        print(f"(当前状态: {session.current_state_id})")

    print("\n--- 对话结束 ---")
