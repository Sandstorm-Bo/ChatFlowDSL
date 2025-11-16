"""
使用测试桩的单元测试

演示如何使用Mock对象进行单元测试，避免外部依赖
"""

import sys
import os
import unittest

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.mocks import MockLLMResponder, MockDatabaseManager
from dsl.dsl_parser import DslParser
from dsl.interpreter import Interpreter
from core.session_manager import SessionManager, Session
from core.action_executor import ActionExecutor


class TestMockLLM(unittest.TestCase):
    """测试Mock LLM功能"""

    def setUp(self):
        """测试前准备"""
        self.mock_llm = MockLLMResponder()

    def test_intent_recognition_product(self):
        """测试产品咨询意图识别"""
        text = "我想买耳机"
        intent = self.mock_llm.recognize_intent(text)
        self.assertEqual(intent, "产品咨询")

    def test_intent_recognition_order(self):
        """测试订单查询意图识别"""
        text = "查询订单A1234567890"
        intent = self.mock_llm.recognize_intent(text)
        self.assertEqual(intent, "订单查询")

    def test_intent_recognition_refund(self):
        """测试退款意图识别"""
        text = "我要退款，质量有问题"
        intent = self.mock_llm.recognize_intent(text)
        self.assertEqual(intent, "退款退货")

    def test_intent_recognition_greeting(self):
        """测试问候意图识别"""
        text = "你好"
        intent = self.mock_llm.recognize_intent(text)
        self.assertEqual(intent, "闲聊问候")

    def test_entity_extraction_order_id(self):
        """测试订单号实体提取"""
        text = "我的订单号是A1234567890"
        entities = self.mock_llm.extract_entities(text)
        self.assertIn("订单号", entities)
        self.assertEqual(entities["订单号"], ["A1234567890"])

    def test_entity_extraction_product_id(self):
        """测试商品ID实体提取"""
        text = "我要买P001和P002"
        entities = self.mock_llm.extract_entities(text)
        self.assertIn("商品ID", entities)
        self.assertEqual(len(entities["商品ID"]), 2)

    def test_generate_response(self):
        """测试Mock回复生成"""
        prompt = "用户询问商品信息"
        response = self.mock_llm.generate_response(prompt)
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)


class TestMockDatabase(unittest.TestCase):
    """测试Mock数据库功能"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = MockDatabaseManager(use_memory=True)

    def tearDown(self):
        """测试后清理"""
        self.mock_db.close()

    def test_get_product_exists(self):
        """测试查询存在的商品"""
        product = self.mock_db.get_product("P001")
        self.assertIsNotNone(product)
        self.assertEqual(product["product_id"], "P001")
        self.assertEqual(product["name"], "蓝牙耳机")
        self.assertEqual(product["price"], 299.00)

    def test_get_product_not_exists(self):
        """测试查询不存在的商品"""
        product = self.mock_db.get_product("P999")
        self.assertIsNone(product)

    def test_list_all_products(self):
        """测试查询所有商品"""
        products = self.mock_db.list_products()
        self.assertGreaterEqual(len(products), 3)

    def test_list_products_by_category(self):
        """测试按分类查询商品"""
        products = self.mock_db.list_products(category="数码配件")
        self.assertGreater(len(products), 0)
        for product in products:
            self.assertEqual(product["category"], "数码配件")

    def test_get_order_exists(self):
        """测试查询存在的订单"""
        order = self.mock_db.get_order("A1234567890")
        self.assertIsNotNone(order)
        self.assertEqual(order["order_id"], "A1234567890")
        self.assertEqual(order["status"], "shipped")

    def test_get_order_not_exists(self):
        """测试查询不存在的订单"""
        order = self.mock_db.get_order("Z9999999999")
        self.assertIsNone(order)

    def test_list_user_orders(self):
        """测试查询用户订单列表"""
        orders = self.mock_db.list_user_orders("U001")
        self.assertGreaterEqual(len(orders), 2)
        for order in orders:
            self.assertEqual(order["user_id"], "U001")


class TestDSLParser(unittest.TestCase):
    """测试DSL解析器"""

    def test_parse_valid_yaml(self):
        """测试解析有效的YAML流程"""
        parser = DslParser("dsl/flows/common/chitchat.yaml")
        flow = parser.get_flow()

        self.assertIsNotNone(flow)
        self.assertEqual(flow.name, "通用闲聊流程")
        self.assertIn("state_start_chitchat", flow._states_by_id)

    def test_get_entry_state(self):
        """测试获取入口状态"""
        parser = DslParser("dsl/flows/common/chitchat.yaml")
        flow = parser.get_flow()
        entry_state = flow.get_entry_state()

        self.assertIsNotNone(entry_state)
        self.assertEqual(entry_state["id"], "state_start_chitchat")

    def test_get_state_by_id(self):
        """测试根据ID获取状态"""
        parser = DslParser("dsl/flows/common/chitchat.yaml")
        flow = parser.get_flow()
        state = flow.get_state("state_start_chitchat")

        self.assertIsNotNone(state)
        self.assertIn("actions", state)


class TestInterpreter(unittest.TestCase):
    """测试解释器"""

    def setUp(self):
        """测试前准备"""
        parser = DslParser("dsl/flows/common/chitchat.yaml")
        self.flow = parser.get_flow()
        self.interpreter = Interpreter(self.flow)
        self.session = Session("test-session")

    def test_process_initial_state(self):
        """测试处理初始状态（chitchat流程会立即转换到end状态）"""
        actions = self.interpreter.process(self.session, "你好")
        self.assertIsInstance(actions, list)

        # chitchat流程设计为无条件转换到end状态
        # 验证会话状态已正确转换
        self.assertEqual(self.session.current_state_id, "state_end_chitchat")

        # end状态的actions为空列表，这是预期的设计
        self.assertEqual(len(actions), 0)

    def test_condition_matching_regex(self):
        """测试正则表达式条件匹配"""
        # 使用私有方法测试（仅用于单元测试）
        condition = {
            "all": [
                {"type": "regex", "value": "你好|hi|hello"}
            ]
        }
        result = self.interpreter._is_condition_met(condition, "你好", self.session)
        self.assertTrue(result)

    def test_condition_matching_variable_equals(self):
        """测试变量比较条件匹配"""
        # 设置会话变量
        self.session.variables["test_var"] = "test_value"

        condition = {
            "all": [
                {"type": "variable_equals", "variable": "test_var", "value": "test_value"}
            ]
        }
        result = self.interpreter._is_condition_met(condition, "测试输入", self.session)
        self.assertTrue(result)

    def test_condition_matching_any(self):
        """测试any逻辑条件匹配"""
        condition = {
            "any": [
                {"type": "regex", "value": "不存在的关键词"},
                {"type": "regex", "value": "你好"}
            ]
        }
        result = self.interpreter._is_condition_met(condition, "你好", self.session)
        self.assertTrue(result)


class TestSessionManager(unittest.TestCase):
    """测试会话管理器"""

    def setUp(self):
        """测试前准备"""
        self.manager = SessionManager(session_timeout=60)

    def test_create_session(self):
        """测试创建会话"""
        session = self.manager.create_session()
        self.assertIsNotNone(session)
        self.assertIsNotNone(session.session_id)

    def test_get_or_create_session(self):
        """测试获取或创建会话"""
        session1 = self.manager.get_session("test-123")
        session2 = self.manager.get_session("test-123")
        self.assertEqual(session1.session_id, session2.session_id)

    def test_session_count(self):
        """测试会话计数"""
        initial_count = self.manager.get_active_session_count()
        self.manager.get_session("test-1")
        self.manager.get_session("test-2")
        new_count = self.manager.get_active_session_count()
        self.assertEqual(new_count, initial_count + 2)

    def test_clear_session(self):
        """测试清除会话"""
        self.manager.get_session("test-to-delete")
        initial_count = self.manager.get_active_session_count()
        self.manager.clear_session("test-to-delete")
        new_count = self.manager.get_active_session_count()
        self.assertEqual(new_count, initial_count - 1)

    def test_session_timeout(self):
        """测试会话超时"""
        import time
        session = self.manager.get_session("test-timeout")
        time.sleep(0.1)
        # 会话应该未过期（超时时间60秒）
        self.assertFalse(session.is_expired(timeout=60))
        # 设置短超时时间测试过期
        self.assertTrue(session.is_expired(timeout=0.05))


class TestSession(unittest.TestCase):
    """测试会话对象"""

    def test_session_variables(self):
        """测试会话变量"""
        session = Session("test-session")
        session.variables["test_key"] = "test_value"
        self.assertEqual(session.variables["test_key"], "test_value")

    def test_session_to_dict(self):
        """测试会话序列化"""
        session = Session("test-session")
        session.current_state_id = "state_test"
        session.variables["key1"] = "value1"
        session_dict = session.to_dict()

        self.assertEqual(session_dict["session_id"], "test-session")
        self.assertEqual(session_dict["current_state_id"], "state_test")
        self.assertIn("key1", session_dict["variables"])

    def test_session_update_activity(self):
        """测试会话活跃时间更新"""
        import time
        session = Session("test-session")
        old_time = session.last_active
        time.sleep(0.01)
        session.update_activity()
        new_time = session.last_active
        self.assertGreater(new_time, old_time)


def run_tests():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("ChatFlow DSL 单元测试（使用测试桩）")
    print("=" * 80 + "\n")

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestMockLLM))
    suite.addTests(loader.loadTestsFromTestCase(TestMockDatabase))
    suite.addTests(loader.loadTestsFromTestCase(TestDSLParser))
    suite.addTests(loader.loadTestsFromTestCase(TestInterpreter))
    suite.addTests(loader.loadTestsFromTestCase(TestSessionManager))
    suite.addTests(loader.loadTestsFromTestCase(TestSession))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 打印总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    print(f"运行测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("=" * 80)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
