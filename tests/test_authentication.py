"""
测试用户认证系统

验证：
1. 数据库用户认证功能
2. 服务器端登录处理
3. 客户端登录流程
4. 会话与用户ID关联
5. 用户特定数据的智能查询
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database_manager import DatabaseManager
from core.session_manager import SessionManager
from core.chatbot import Chatbot
import unittest


class TestDatabaseAuthentication(unittest.TestCase):
    """测试数据库认证功能"""

    def setUp(self):
        """每个测试前创建新的数据库实例"""
        # 使用临时数据库
        self.db = DatabaseManager(db_path="data/test_chatbot.db")

    def tearDown(self):
        """清理测试数据库"""
        if os.path.exists("data/test_chatbot.db"):
            os.remove("data/test_chatbot.db")

    def test_authenticate_user_success(self):
        """测试用户认证成功"""
        print("\n[测试] 用户认证成功")

        user_data = self.db.authenticate_user("张三", "password123")

        self.assertIsNotNone(user_data, "认证应该成功")
        self.assertEqual(user_data["user_id"], "U001")
        self.assertEqual(user_data["username"], "张三")
        self.assertNotIn("password", user_data, "返回的用户数据不应包含密码")
        print(f"✓ 用户 '张三' 认证成功，user_id={user_data['user_id']}")

    def test_authenticate_user_wrong_password(self):
        """测试错误密码"""
        print("\n[测试] 错误密码")

        user_data = self.db.authenticate_user("张三", "wrong_password")

        self.assertIsNone(user_data, "错误密码应该认证失败")
        print("✓ 错误密码认证失败（符合预期）")

    def test_authenticate_user_nonexistent(self):
        """测试不存在的用户"""
        print("\n[测试] 不存在的用户")

        user_data = self.db.authenticate_user("不存在的用户", "password")

        self.assertIsNone(user_data, "不存在的用户应该认证失败")
        print("✓ 不存在的用户认证失败（符合预期）")

    def test_get_user_by_username(self):
        """测试通过用户名获取用户"""
        print("\n[测试] 通过用户名获取用户")

        user_data = self.db.get_user_by_username("李四")

        self.assertIsNotNone(user_data)
        self.assertEqual(user_data["user_id"], "U002")
        self.assertEqual(user_data["username"], "李四")
        print(f"✓ 成功获取用户 '李四'，user_id={user_data['user_id']}")

    def test_get_user_orders_by_user_id(self):
        """测试获取用户订单"""
        print("\n[测试] 获取用户订单")

        # 测试用户U001的订单
        orders = self.db.get_user_orders("U001")

        self.assertGreater(len(orders), 0, "用户U001应该有订单")
        print(f"✓ 用户U001有 {len(orders)} 个订单")

        for order in orders:
            print(f"  - {order['order_id']}: {order['product_name']} ({order['status']})")


class TestSessionWithAuthentication(unittest.TestCase):
    """测试会话与用户认证的集成"""

    def setUp(self):
        self.session_manager = SessionManager()

    def test_session_with_user_id(self):
        """测试会话关联用户ID"""
        print("\n[测试] 会话关联用户ID")

        session = self.session_manager.get_session("test-session-1", user_id="U001")

        self.assertEqual(session.session_id, "test-session-1")
        self.assertEqual(session.user_id, "U001")
        print(f"✓ 会话 {session.session_id} 成功关联用户 {session.user_id}")

    def test_session_user_id_update(self):
        """测试会话用户ID更新"""
        print("\n[测试] 会话用户ID更新")

        # 第一次获取会话，不提供user_id
        session = self.session_manager.get_session("test-session-2")
        self.assertIsNone(session.user_id)
        print(f"  初始会话user_id: {session.user_id}")

        # 第二次获取同一会话，提供user_id
        session = self.session_manager.get_session("test-session-2", user_id="U002")
        self.assertEqual(session.user_id, "U002")
        print(f"✓ 会话user_id已更新: {session.user_id}")

    def test_session_to_dict_includes_user_id(self):
        """测试会话字典包含user_id"""
        print("\n[测试] 会话字典包含user_id")

        session = self.session_manager.get_session("test-session-3", user_id="U003")
        session_dict = session.to_dict()

        self.assertIn("user_id", session_dict)
        self.assertEqual(session_dict["user_id"], "U003")
        print(f"✓ 会话字典包含user_id: {session_dict['user_id']}")


class TestUserSpecificDataQuery(unittest.TestCase):
    """测试用户特定数据查询"""

    def setUp(self):
        self.db = DatabaseManager(db_path="data/test_chatbot.db")

    def tearDown(self):
        if os.path.exists("data/test_chatbot.db"):
            os.remove("data/test_chatbot.db")

    def test_get_user_specific_orders(self):
        """测试获取特定用户的订单"""
        print("\n[测试] 获取特定用户的订单")

        # 获取用户U001的订单
        u001_orders = self.db.get_user_orders("U001")
        # 获取用户U002的订单
        u002_orders = self.db.get_user_orders("U002")

        print(f"  用户U001有 {len(u001_orders)} 个订单")
        print(f"  用户U002有 {len(u002_orders)} 个订单")

        # 验证订单属于正确的用户
        for order in u001_orders:
            self.assertEqual(order["user_id"], "U001")
            print(f"    ✓ 订单 {order['order_id']} 属于用户U001")

        for order in u002_orders:
            self.assertEqual(order["user_id"], "U002")
            print(f"    ✓ 订单 {order['order_id']} 属于用户U002")


class TestChatbotWithAuthentication(unittest.TestCase):
    """测试聊天机器人与认证的集成"""

    def setUp(self):
        self.chatbot = Chatbot(flows_dir="dsl/flows")

    def test_chatbot_accepts_user_id(self):
        """测试聊天机器人接受user_id参数"""
        print("\n[测试] 聊天机器人接受user_id参数")

        # 使用user_id调用handle_message
        responses = self.chatbot.handle_message(
            session_id="test-auth-session",
            user_input="你好",
            user_id="U001"
        )

        self.assertIsNotNone(responses)
        self.assertGreater(len(responses), 0)
        print(f"✓ 聊天机器人成功处理带user_id的消息")
        print(f"  响应: {responses[0]}")

    def test_session_retains_user_id(self):
        """测试会话保留user_id"""
        print("\n[测试] 会话保留user_id")

        session_id = "test-auth-session-2"

        # 第一次消息，提供user_id
        self.chatbot.handle_message(session_id, "你好", user_id="U002")

        # 获取会话，检查user_id
        session = self.chatbot.session_manager.get_session(session_id)
        self.assertEqual(session.user_id, "U002")
        print(f"✓ 会话保留了user_id: {session.user_id}")


def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("ChatFlowDSL 用户认证系统测试套件")
    print("=" * 80)

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseAuthentication))
    suite.addTests(loader.loadTestsFromTestCase(TestSessionWithAuthentication))
    suite.addTests(loader.loadTestsFromTestCase(TestUserSpecificDataQuery))
    suite.addTests(loader.loadTestsFromTestCase(TestChatbotWithAuthentication))

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

    if result.wasSuccessful():
        print("\n✓ 所有测试通过！")
        return 0
    else:
        print("\n✗ 部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
