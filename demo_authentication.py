"""
用户认证系统演示脚本

展示新增的用户登录和认证功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database_manager import DatabaseManager
from core.session_manager import SessionManager
from core.chatbot import Chatbot


def print_banner(text):
    """打印美化的标题"""
    print(f"\n{'='*80}")
    print(f"  {text}")
    print(f"{'='*80}\n")


def demo_database_authentication():
    """演示1: 数据库用户认证"""
    print_banner("演示1: 数据库用户认证")

    db = DatabaseManager()

    # 测试用例
    test_cases = [
        {"username": "张三", "password": "password123", "should_pass": True},
        {"username": "李四", "password": "password456", "should_pass": True},
        {"username": "张三", "password": "wrong_password", "should_pass": False},
        {"username": "不存在的用户", "password": "password", "should_pass": False},
    ]

    for case in test_cases:
        username = case["username"]
        password = case["password"]
        should_pass = case["should_pass"]

        print(f"尝试登录: username={username}, password={password}")

        user_data = db.authenticate_user(username, password)

        if user_data:
            print(f"  [成功] 用户 {username} 认证成功")
            print(f"    user_id: {user_data['user_id']}")
            print(f"    email: {user_data.get('email', 'N/A')}")
            print(f"    phone: {user_data.get('phone', 'N/A')}")
            assert should_pass, f"预期认证失败，但实际成功: {username}"
        else:
            print(f"  [失败] 用户 {username} 认证失败")
            assert not should_pass, f"预期认证成功，但实际失败: {username}"

        print()

    print("数据库认证测试完成！")


def demo_session_with_user():
    """演示2: 会话关联用户"""
    print_banner("演示2: 会话关联用户")

    session_manager = SessionManager()

    # 创建会话并关联用户
    print("创建会话并关联用户...")
    session1 = session_manager.get_session("session-001", user_id="U001")
    session2 = session_manager.get_session("session-002", user_id="U002")

    print(f"会话1: session_id={session1.session_id}, user_id={session1.user_id}")
    print(f"会话2: session_id={session2.session_id}, user_id={session2.user_id}")

    # 验证会话字典包含user_id
    print("\n验证会话字典包含user_id...")
    session1_dict = session1.to_dict()
    print(f"会话1字典: {session1_dict}")
    assert "user_id" in session1_dict
    assert session1_dict["user_id"] == "U001"

    print("\n会话关联用户测试完成！")


def demo_user_specific_orders():
    """演示3: 用户特定订单查询"""
    print_banner("演示3: 用户特定订单查询（智能自动查询）")

    db = DatabaseManager()

    print("场景: 用户登录后，系统自动查询该用户的订单\n")

    # 查询不同用户的订单
    users = ["U001", "U002", "U003"]

    for user_id in users:
        user = db.get_user(user_id)
        if user:
            print(f"用户: {user['username']} (user_id={user_id})")
        else:
            print(f"用户ID: {user_id}")

        orders = db.get_user_orders(user_id)

        if orders:
            print(f"  订单数量: {len(orders)}")
            for order in orders:
                print(f"    - {order['order_id']}: {order['product_name']} [{order['status']}]")
        else:
            print(f"  无订单记录")

        print()

    print("用户特定订单查询测试完成！")
    print("注意: 系统现在可以根据登录用户自动查询其订单，无需用户提供订单号！")


def demo_chatbot_with_user():
    """演示4: 带用户认证的聊天机器人"""
    print_banner("演示4: 带用户认证的聊天机器人")

    chatbot = Chatbot(flows_dir="dsl/flows")

    # 模拟用户U001的对话
    print("模拟用户U001（张三）的对话:\n")

    test_messages = [
        "你好",
        "我要查询订单",
    ]

    session_id = "demo-session-u001"
    user_id = "U001"

    for message in test_messages:
        print(f"用户(U001-张三): {message}")

        # 调用chatbot时传入user_id
        responses = chatbot.handle_message(session_id, message, user_id=user_id)

        print(f"系统:")
        for response in responses:
            print(f"  {response}")
        print()

    # 验证会话保留了user_id
    session = chatbot.session_manager.get_session(session_id)
    print(f"会话信息:")
    print(f"  session_id: {session.session_id}")
    print(f"  user_id: {session.user_id}")
    print(f"  当前状态: {session.current_state_id}")

    print("\n带用户认证的聊天机器人测试完成！")


def demo_smart_query():
    """演示5: 智能自动查询（核心功能）"""
    print_banner("演示5: 智能自动查询 - 问题解决方案")

    print('问题描述:')
    print('  用户问: "我的水杯什么时候发货"')
    print('  旧系统: 无法识别是哪个用户，无法自动查询')
    print('  新系统: 已登录用户，系统自动查询该用户的订单！\n')

    print('解决方案:')
    print('  1. 用户登录时，服务器验证用户名密码')
    print('  2. 服务器保存 session_id -> user_id 映射')
    print('  3. 用户发送消息时，消息自动携带user_id')
    print('  4. Chatbot调用ActionExecutor时，session中包含user_id')
    print('  5. ActionExecutor查询订单时，自动使用session中的user_id')
    print('  6. 返回该用户的所有订单，无需用户提供订单号！\n')

    db = DatabaseManager()

    # 模拟场景
    print('实际演示:')
    print('  假设用户U001（张三）已登录\n')

    # 模拟session包含user_id
    mock_session = {
        "session_id": "demo-session",
        "user_id": "U001",  # 关键：session中包含user_id
        "variables": {}
    }

    print(f'Session信息: {mock_session}\n')

    # 智能查询：自动从session中获取user_id
    print('执行智能查询: 获取该用户的所有订单')
    user_id = mock_session.get("user_id")
    orders = db.get_user_orders(user_id)

    print(f'查询结果: 找到 {len(orders)} 个订单\n')

    for order in orders:
        print(f'  订单: {order["order_id"]}')
        print(f'    商品: {order["product_name"]}')
        print(f'    状态: {order["status"]}')
        print(f'    物流: {order.get("tracking_number", "待发货")}')
        print()

    print('总结:')
    print('  通过用户认证，系统可以自动识别用户身份')
    print('  当用户问"我的订单"时，无需用户提供订单号')
    print('  系统自动查询该用户的所有订单，实现智能化服务！')


def main():
    """主函数"""
    print("\n")
    print("╔" + "═"*78 + "╗")
    print("║" + " "*24 + "ChatFlowDSL 用户认证演示" + " "*24 + "║")
    print("║" + " "*78 + "║")
    print("║" + " "*18 + "用户登录 + 智能自动查询" + " "*18 + "║")
    print("╚" + "═"*78 + "╝")

    print("\n请选择演示模式：")
    print("  1. 数据库用户认证")
    print("  2. 会话关联用户")
    print("  3. 用户特定订单查询")
    print("  4. 带用户认证的聊天机器人")
    print("  5. 智能自动查询（核心功能）")
    print("  0. 运行所有演示")

    choice = input("\n请输入选项 (0-5): ").strip()

    if choice == "1":
        demo_database_authentication()
    elif choice == "2":
        demo_session_with_user()
    elif choice == "3":
        demo_user_specific_orders()
    elif choice == "4":
        demo_chatbot_with_user()
    elif choice == "5":
        demo_smart_query()
    elif choice == "0":
        demo_database_authentication()
        demo_session_with_user()
        demo_user_specific_orders()
        demo_chatbot_with_user()
        demo_smart_query()
    else:
        print("无效选项")

    print("\n" + "="*80)
    print("  演示结束！")
    print("="*80)
    print("\n说明:")
    print("  - 测试用户: 张三(password123), 李四(password456), 王五(password789)")
    print("  - 客户端启动时会提示登录")
    print("  - 服务器会验证用户凭证并保存用户信息")
    print("  - 所有消息自动携带user_id，实现智能查询")
    print()


if __name__ == "__main__":
    main()
