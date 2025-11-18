import os
import sys
import unittest

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.chatbot import Chatbot


class _QueueLLMResponder:
    """A simple LLM stub that returns a preset intent with high confidence."""

    def __init__(self):
        self.next_intent = None

    def set_next_intent(self, intent: str):
        self.next_intent = intent

    def recognize_intent(self, user_input: str, available_intents=None):
        return {
            "intent": self.next_intent,
            "confidence": 0.9,
            "reasoning": "mock"
        }


class TestSessionPersistence(unittest.TestCase):
    def test_order_flow_preserves_session_state(self):
        chatbot = Chatbot()
        session_id = "session-preserve"

        # Kick off the order management flow and advance to the collection state
        chatbot.handle_message(session_id, "我想查询物流信息")
        chatbot.handle_message(session_id, "继续")

        # Provide an order id to trigger extraction and DB lookup
        responses = chatbot.handle_message(session_id, "订单号是A1234567890")
        session = chatbot.session_manager.get_session(session_id)

        self.assertEqual(session.get("active_flow_name"), "售中订单管理流程")
        self.assertEqual(session.current_state_id, "state_query_specific_order")
        self.assertEqual(session.variables.get("order_id"), "A1234567890")
        self.assertIn("current_order", session.variables)
        self.assertEqual(session.last_user_input, "订单号是A1234567890")
        self.assertGreater(len(responses), 0)


class TestLLMIntentFlowSelection(unittest.TestCase):
    def test_llm_intent_map_uses_loaded_flows(self):
        llm = _QueueLLMResponder()
        chatbot = Chatbot(llm_responder=llm)

        expected_intents = {
            "售前产品咨询流程": "用户想了解产品信息、查看商品详情、询问价格和功能",
            "售中订单管理流程": "用户想查询订单状态、查看物流信息、取消订单",
            "标准退款流程": "用户想申请退款或退货、反馈商品质量问题",
            "发票服务流程": "用户需要开具发票、提供发票抬头和税号",
            "耳机故障排查流程": "用户反馈耳机故障、设备连接问题、需要技术支持",
            "通用闲聊流程": "用户打招呼、闲聊、问候",
        }

        self.assertEqual(set(chatbot.flow_intents.keys()), set(chatbot.flows.keys()))

        for idx, (flow_name, description) in enumerate(expected_intents.items()):
            self.assertEqual(chatbot.flow_intents.get(flow_name), description)

            llm.set_next_intent(description)
            session_id = f"llm-session-{idx}"
            chatbot.handle_message(session_id, "llm 意图测试")
            session = chatbot.session_manager.get_session(session_id)

            self.assertEqual(session.get("active_flow_name"), flow_name)


if __name__ == "__main__":
    unittest.main()
