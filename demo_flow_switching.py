"""
流程切换功能演示脚本

展示修复后的全局流程切换机制，解决"通用闲聊流程死锁"问题
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.chatbot import Chatbot
from core.database_manager import DatabaseManager


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

    print("测试用例：")
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

    print("\n" + "="*80)
    print("  测试总结")
    print("="*80)
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
        email="test001@example.com"
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
    result2 = db.register_user(
        username="测试用户001",
        password="another_password"
    )

    if result2["success"]:
        print(f"   [异常] 不应该允许重复注册")
    else:
        print(f"   [正确] {result2['message']}")

    print("\n用户注册功能测试完成！")


def demo_user_specific_query():
    """演示：基于用户身份的智能查询"""
    print_banner("演示：智能用户识别与自动查询")

    chatbot = Chatbot(flows_dir="dsl/flows")
    db = DatabaseManager()

    print("核心功能: 当用户问'我的水杯什么时候发货'时")
    print("  系统自动识别登录用户身份，查询该用户的订单\n")

    # 测试不同用户
    test_users = [
        ("U001", "张三"),
        ("U002", "李四"),
        ("U003", "王五")
    ]

    for user_id, username in test_users:
        print(f"\n{'='*80}")
        print(f"模拟用户: {username} (user_id={user_id})")
        print(f"{'='*80}")

        session_id = f"demo-query-{user_id}"

        # 用户询问订单
        message = "我的订单"

        print(f"用户输入: '{message}'\n")

        responses = chatbot.handle_message(session_id, message, user_id=user_id)

        print(f"系统响应:")
        for response in responses:
            print(f"  {response}")

    print("\n" + "="*80)
    print("  说明")
    print("="*80)
    print("注意观察:")
    print("  - 张三(U001): 有2个订单")
    print("  - 李四(U002): 有1个订单")
    print("  - 王五(U003): 无订单")
    print("\n系统自动根据登录用户的user_id查询数据库，无需用户提供订单号！")


def main():
    """主函数"""
    print("\n")
    print("╔" + "═"*78 + "╗")
    print("║" + " "*24 + "ChatFlowDSL 功能修复演示" + " "*24 + "║")
    print("║" + " "*78 + "║")
    print("║" + " "*15 + "1. 全局流程切换  2. 用户注册  3. 智能查询" + " "*15 + "║")
    print("╚" + "═"*78 + "╝")

    print("\n请选择演示模式：")
    print("  1. 全局流程切换（修复通用闲聊死锁）")
    print("  2. 用户注册功能")
    print("  3. 智能用户识别与自动查询")
    print("  0. 运行所有演示")

    choice = input("\n请输入选项 (0-3): ").strip()

    if choice == "1":
        demo_flow_switching()
    elif choice == "2":
        demo_registration()
    elif choice == "3":
        demo_user_specific_query()
    elif choice == "0":
        demo_flow_switching()
        demo_registration()
        demo_user_specific_query()
    else:
        print("无效选项")

    print("\n" + "="*80)
    print("  演示结束！")
    print("="*80)
    print("\n关键改进:")
    print("  1. ✓ 全局流程切换：用户可随时通过关键词切换业务流程")
    print("  2. ✓ 用户注册：新用户可以自助注册账号")
    print("  3. ✓ 智能查询：系统自动识别用户身份，无需提供订单号")
    print()


if __name__ == "__main__":
    main()
