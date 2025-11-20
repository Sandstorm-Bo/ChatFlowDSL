"""
用户认证系统演示脚本

展示新增的用户登录和认证功能
"""

import sys
import os

# 添加项目根目录到Python路径
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

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

    assert session1_dict["user_id"] == "U001"
    print("\n会话关联用户测试完成！")


def demo_chatbot_with_user_context():
    """演示3: 基于用户身份的对话"""
    print_banner("演示3: 基于用户身份的对话")

    chatbot = Chatbot(flows_dir="dsl/flows")
    session_id = "session-auth-demo"
    user_id = "U001"

    messages = [
        "你好",
        "查询我的订单",
        "上周买的耳机",
    ]

    for msg in messages:
        print(f"\n👤 用户: {msg}")
        responses = chatbot.handle_message(session_id, msg, user_id=user_id)
        for resp in responses:
            print(f"🤖 系统: {resp}")


def main():
    demo_database_authentication()
    demo_session_with_user()
    demo_chatbot_with_user_context()


if __name__ == "__main__":
    main()

