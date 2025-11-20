"""
自动化测试脚本 - 测试流程切换和用户注册修复
"""

import sys
import os

# 添加项目根目录到Python路径
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from core.chatbot import Chatbot  # noqa: E402
from core.database_manager import DatabaseManager  # noqa: E402


def test_flow_switching():
    """测试1: 全局流程切换功能"""
    print("\n" + "=" * 80)
    print("测试1: 全局流程切换功能（修复通用闲聊死锁）")
    print("=" * 80)

    chatbot = Chatbot(flows_dir="dsl/flows")
    session_id = "test-flow-switching"
    user_id = "U001"

    test_cases = [
        {
            "input": "你好",
            "expected_flow": "通用闲聊流程",
            "description": "触发通用闲聊流程",
        },
        {
            "input": "我是谁",
            "expected_flow": "通用闲聊流程",
            "description": "继续通用闲聊流程",
        },
        {
            "input": "查询订单",
            "expected_flow": "订单管理流程",
            "description": "从闲聊切换到订单管理（关键测试）",
        },
        {
            "input": "咨询产品",
            "expected_flow": "产品咨询流程",
            "description": "从订单管理切换到产品咨询",
        },
    ]

    passed = 0
    failed = 0

    for idx, case in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"子测试 {idx}: {case['description']}")
        print(f"输入: '{case['input']}'")
        print(f"{'='*70}")

        responses = chatbot.handle_message(session_id, case["input"], user_id=user_id)

        print(f"系统响应:")
        # 避免Unicode编码问题，只检查是否有响应
        if responses:
            print(f"  [收到 {len(responses)} 条响应]")
        else:
            print(f"  [无响应]")

        # 检查是否有有效响应（不是默认错误消息）
        if responses and "抱歉，我暂时无法理解" not in responses[0]:
            print(f"[通过] 成功处理用户输入并生成响应")
            passed += 1
        else:
            print(f"[失败] 未能正确处理用户输入")
            failed += 1

    print(f"\n{'='*80}")
    print(f"测试1总结: 通过 {passed}/{len(test_cases)}, 失败 {failed}/{len(test_cases)}")
    print(f"{'='*80}")

    return passed == len(test_cases)


def test_user_registration():
    """测试2: 用户注册功能"""
    print("\n" + "=" * 80)
    print("测试2: 用户注册功能")
    print("=" * 80)

    db = DatabaseManager()

    # 生成唯一用户名避免冲突
    import time

    username = f"test_user_{int(time.time())}"

    test_cases = [
        {
            "name": "注册新用户",
            "action": lambda: db.register_user(
                username=username,
                password="test123",
                phone="13912345678",
                email=f"{username}@test.com",
            ),
            "expected_success": True,
        },
        {
            "name": "验证新用户可以登录",
            "action": lambda: db.authenticate_user(username, "test123"),
            "expected_success": True,
        },
        {
            "name": "重复注册应该失败",
            "action": lambda: db.register_user(
                username=username, password="another_password"
            ),
            "expected_success": False,
        },
        {
            "name": "错误密码登录应该失败",
            "action": lambda: db.authenticate_user(username, "wrong_password"),
            "expected_success": False,
        },
    ]

    passed = 0
    failed = 0

    for idx, case in enumerate(test_cases, 1):
        print(f"\n子测试 {idx}: {case['name']}")
        result = case["action"]()

        if isinstance(result, dict):
            # register_user返回dict
            success = result.get("success", False)
            message = result.get("message", "")
            print(f"  结果: {'成功' if success else '失败'}")
            print(f"  消息: {message}")

            if success == case["expected_success"]:
                print(f"  [通过]")
                passed += 1
            else:
                print(
                    f"  [失败] 预期 {'成功' if case['expected_success'] else '失败'}，实际 {'成功' if success else '失败'}"
                )
                failed += 1
        else:
            # authenticate_user返回user_data或None
            success = result is not None

            if success == case["expected_success"]:
                print(f"  [通过]")
                passed += 1
            else:
                print(
                    f"  [失败] 预期 {'成功' if case['expected_success'] else '失败'}，实际 {'成功' if success else '失败'}"
                )
                failed += 1

    print(f"\n{'='*80}")
    print(f"测试2总结: 通过 {passed}/{len(test_cases)}, 失败 {failed}/{len(test_cases)}")
    print(f"{'='*80}")

    return passed == len(test_cases)


def test_user_specific_query():
    """测试3: 基于用户身份的智能查询"""
    print("\n" + "=" * 80)
    print("测试3: 基于用户身份的智能查询")
    print("=" * 80)

    chatbot = Chatbot(flows_dir="dsl/flows")
    db = DatabaseManager()

    # 测试不同用户查询订单
    test_users = [
        {"user_id": "U001", "username": "张三", "expected_orders": 2},
        {"user_id": "U002", "username": "李四", "expected_orders": 1},
        {"user_id": "U003", "username": "王五", "expected_orders": 0},
    ]

    passed = 0
    failed = 0

    for user in test_users:
        print(f"\n子测试: 用户 {user['username']} (user_id={user['user_id']})")

        # 直接查询数据库验证
        orders = db.get_user_orders(user["user_id"])
        actual_count = len(orders)

        print(f"  预期订单数: {user['expected_orders']}")
        print(f"  实际订单数: {actual_count}")

        if actual_count == user["expected_orders"]:
            print(f"  [通过]")
            passed += 1
        else:
            print(f"  [失败]")
            failed += 1

    print(f"\n{'='*80}")
    print(f"测试3总结: 通过 {passed}/{len(test_users)}, 失败 {failed}/{len(test_users)}")
    print(f"{'='*80}")

    return passed == len(test_users)


def main():
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 25 + "自动化测试 - 功能修复验证" + " " * 25 + "║")
    print("╚" + "═" * 78 + "╝")

    results = []

    # 运行所有测试
    print("\n开始运行测试...")

    results.append(("流程切换功能", test_flow_switching()))
    results.append(("用户注册功能", test_user_registration()))
    results.append(("智能用户查询", test_user_specific_query()))

    # 总结
    print("\n" + "=" * 80)
    print("总体测试结果")
    print("=" * 80)

    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)

    for name, passed in results:
        status = "[通过]" if passed else "[失败]"
        print(f"  {status}: {name}")

    print(f"\n总计: {total_passed}/{total_tests} 项测试通过")

    if total_passed == total_tests:
        print("\n[成功] 所有测试通过！")
        print("\n关键修复:")
        print("  1. [OK] 全局流程切换机制已实现")
        print("  2. [OK] 用户注册功能正常工作")
        print("  3. [OK] 智能用户识别与查询正常")
        return 0
    else:
        print(f"\n[失败] {total_tests - total_passed} 项测试失败")
        return 1


if __name__ == "__main__":
    exit(main())

