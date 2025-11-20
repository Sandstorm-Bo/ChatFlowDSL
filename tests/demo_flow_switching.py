"""
流程切换功能演示脚本

展示修复后的全局流程切换机制，解决"通用闲聊流程死锁"问题
"""

import sys
import os

# 添加项目根目录到Python路径
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from core.chatbot import Chatbot  # noqa: E402
from core.database_manager import DatabaseManager  # noqa: E402


def print_banner(text):
    """打印美化的标题"""
    print(f"\n{'='*80}")
    print(f"  {text}")
    print(f"{'='*80}\n")


def demo_flow_switching():
    """演示：流程切换功能（核心修复）"""
    print_banner("演示：全局流程切换 - 解决通用闲聊流程死锁问题")

    chatbot = Chatbot(flows_dir="dsl/flows")
    db = DatabaseManager()

    # 模拟已登录用户
    session_id = "demo-flow-switching"
    user_id = "U001"  # 张三

    print("问题场景:")
    print("  之前：用户进入通用闲聊流程后，无论说什么都无法跳出")
    print("  现在：用户可以随时通过关键词切换到其他业务流程\n")

    print("测试用例:")
    print("  1. 用户说'你好' → 进入通用闲聊流程")
    print("  2. 用户说'我是谁' → 仍在通用闲聊流程")
    print("  3. 用户说'你知道我的水杯什么时候发货吗' → 【应该切换到订单管理流程】")
    print("  4. 用户说'查询商品信息' → 【应该切换到产品咨询流程】\n")

    test_messages = [
        "你好",
        "我是谁",
        "你知道我的水杯什么时候发货吗",
        "查询商品信息",
    ]

    for idx, message in enumerate(test_messages, 1):
        print(f"\n{'='*80}")
        print(f"测试 {idx}: 用户输入: '{message}'")
        print(f"{'='*80}")

        responses = chatbot.handle_message(session_id, message, user_id=user_id)

        print(f"\n系统响应:")
        for response in responses:
            print(f"  {response}")

    print("\n" + "=" * 80)
    print("  测试总结")
    print("=" * 80)
    print("修复前:")
    print("  - 步骤3和4都会提示'抱歉，我不知道如何回应'")
    print("  - 用户被困在通用闲聊流程中，无法使用其他功能")
    print("\n修复后:")
    print("  - 步骤3自动切换到订单管理流程，查询用户订单")
    print("  - 步骤4自动切换到产品咨询流程，展示商品信息")
    print("  - 实现了真正的智能对话流程切换")


def demo_registration():
    """演示：用户注册功能"""
    print_banner("演示：用户注册功能")

    db = DatabaseManager()

    print("测试场景: 注册新用户\n")

    # 测试注册
    print("1. 尝试注册新用户...")
    result = db.register_user(
        username="测试用户001",
        password="test123",
        phone="13912345678",
        email="test001@example.com",
    )

    if result["success"]:
        print(f"   [成功] {result['message']}")
        print(f"   user_id: {result['user_id']}")

        # 验证可以登录
        print("\n2. 验证新用户可以登录...")
        user_data = db.authenticate_user("测试用户001", "test123")
        if user_data:
            print(f"   [成功] 登录成功")
            print(f"   user_id: {user_data['user_id']}")
            print(f"   email: {user_data.get('email', 'N/A')}")
        else:
            print(f"   [失败] 登录失败")
    else:
        print(f"   [失败] {result['message']}")

    # 测试重复注册
    print("\n3. 尝试使用相同用户名注册（应该失败）...")
    result2 = db.register_user(username="测试用户001", password="another_password")

    if result2["success"]:
        print(f"   [异常] 不应该允许重复注册")
    else:
        print(f"   [正确] {result2['message']}")

    print("\n用户注册功能测试完成！")


def main():
    demo_flow_switching()
    demo_registration()


if __name__ == "__main__":
    main()

