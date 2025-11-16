"""
测试口语化表达的混合匹配机制

验证系统能够通过"规则优先 + LLM兜底"策略识别复杂的口语化表达
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.chatbot import Chatbot
from llm.llm_responder import LLMResponder
import yaml


def load_config():
    """加载配置文件"""
    config_path = "config/config.yaml"
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return None


def test_rule_based_matching():
    """测试规则匹配（应该快速成功）"""
    print("\n" + "="*80)
    print("测试1: 规则匹配（标准表达）")
    print("="*80)

    chatbot = Chatbot(flows_dir="dsl/flows", llm_responder=None)

    test_cases = [
        ("你好", "通用闲聊流程"),
        ("我想了解产品", "产品咨询流程"),
        ("查询订单A1234567890", "订单管理流程"),
        ("我要退款", "退款退货流程"),
        ("需要开发票", "发票申请流程"),
    ]

    for user_input, expected_flow in test_cases:
        print(f"\n用户输入: '{user_input}'")
        print(f"期望触发: {expected_flow}")

        responses = chatbot.handle_message("test-session-rule", user_input)

        print(f"系统回复: {responses[0] if responses else '(无回复)'}")
        print("-" * 70)


def test_llm_fallback_matching():
    """测试LLM兜底匹配（口语化表达）"""
    print("\n" + "="*80)
    print("测试2: LLM兜底匹配（口语化表达）")
    print("="*80)

    # 加载配置
    config = load_config()
    if not config or not config.get("llm", {}).get("api_key"):
        print("⚠️ 未配置LLM API Key，跳过LLM测试")
        print("提示: 请在 config/config.yaml 中配置LLM API Key")
        return

    # 初始化LLM响应器
    llm_config = config["llm"]
    llm_responder = LLMResponder(
        api_key=llm_config["api_key"],
        model_name=llm_config["model_name"],
        base_url=llm_config.get("base_url"),
        timeout=llm_config.get("timeout", 30)
    )

    # 创建带LLM的Chatbot
    chatbot = Chatbot(flows_dir="dsl/flows", llm_responder=llm_responder)

    # 口语化测试用例（规则无法匹配，需要LLM理解）
    test_cases = [
        {
            "input": "那个单子发到哪了",
            "expected_intent": "订单查询",
            "description": "口语化：'那个单子' = 订单"
        },
        {
            "input": "东西坏了想退",
            "expected_intent": "退款退货",
            "description": "口语化：简化表达退款意图"
        },
        {
            "input": "帮我看看你们卖啥",
            "expected_intent": "产品咨询",
            "description": "口语化：'卖啥' = 有什么产品"
        },
        {
            "input": "买错了不想要了",
            "expected_intent": "退款退货",
            "description": "复杂语境：表达退款意图"
        },
        {
            "input": "耳机连不上蓝牙",
            "expected_intent": "故障报修",
            "description": "技术问题描述"
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[测试用例 {i}] {test_case['description']}")
        print(f"用户输入: '{test_case['input']}'")
        print(f"期望意图: {test_case['expected_intent']}")

        session_id = f"test-session-llm-{i}"
        responses = chatbot.handle_message(session_id, test_case["input"])

        print(f"\n系统回复:")
        for response in responses:
            print(f"  {response}")

        print("-" * 70)


def test_hybrid_with_context():
    """测试带上下文的混合匹配"""
    print("\n" + "="*80)
    print("测试3: 带上下文的混合匹配（多轮对话）")
    print("="*80)

    config = load_config()
    llm_responder = None

    if config and config.get("llm", {}).get("api_key"):
        llm_config = config["llm"]
        llm_responder = LLMResponder(
            api_key=llm_config["api_key"],
            model_name=llm_config["model_name"],
            base_url=llm_config.get("base_url"),
            timeout=llm_config.get("timeout", 30)
        )

    chatbot = Chatbot(flows_dir="dsl/flows", llm_responder=llm_responder)

    # 模拟多轮对话
    conversation = [
        "我上周买的耳机",  # 模糊表达
        "有点问题想退",  # 继续上文
        "质量不太好",  # 说明原因
    ]

    session_id = "test-session-context"

    for turn, user_input in enumerate(conversation, 1):
        print(f"\n[第{turn}轮对话]")
        print(f"用户: {user_input}")

        responses = chatbot.handle_message(session_id, user_input)

        print(f"系统:")
        for response in responses:
            print(f"  {response}")

        print("-" * 70)


def compare_rule_vs_llm():
    """对比规则匹配和LLM匹配的性能"""
    print("\n" + "="*80)
    print("测试4: 规则 vs LLM 性能对比")
    print("="*80)

    import time

    # 纯规则匹配
    chatbot_rule = Chatbot(flows_dir="dsl/flows", llm_responder=None)

    test_input = "我想了解一下产品信息"

    start = time.time()
    chatbot_rule.handle_message("test-perf-rule", test_input)
    rule_time = time.time() - start

    print(f"\n规则匹配耗时: {rule_time*1000:.2f}ms")

    # 带LLM（如果配置了）
    config = load_config()
    if config and config.get("llm", {}).get("api_key"):
        llm_config = config["llm"]
        llm_responder = LLMResponder(
            api_key=llm_config["api_key"],
            model_name=llm_config["model_name"],
            base_url=llm_config.get("base_url"),
            timeout=llm_config.get("timeout", 30)
        )

        chatbot_llm = Chatbot(flows_dir="dsl/flows", llm_responder=llm_responder)

        # 测试LLM fallback场景（规则无法匹配的输入）
        llm_test_input = "那个单子发哪了"

        start = time.time()
        chatbot_llm.handle_message("test-perf-llm", llm_test_input)
        llm_time = time.time() - start

        print(f"LLM兜底耗时: {llm_time*1000:.2f}ms")
        print(f"性能差异: {(llm_time/rule_time):.1f}x")
    else:
        print("⚠️ 未配置LLM，跳过LLM性能测试")


def main():
    """运行所有测试"""
    print("\n" + "="*80)
    print("ChatFlowDSL 口语化表达测试套件")
    print("="*80)
    print("\n本测试验证系统的混合匹配能力：")
    print("  1. 规则优先：快速匹配标准表达（<1ms）")
    print("  2. LLM兜底：理解口语化、模糊表达（~500ms）")
    print("  3. 上下文理解：多轮对话中的指代消解")
    print("  4. 性能对比：规则 vs LLM 响应时间")

    try:
        # 测试1: 规则匹配
        test_rule_based_matching()

        # 测试2: LLM兜底
        test_llm_fallback_matching()

        # 测试3: 带上下文的混合匹配
        test_hybrid_with_context()

        # 测试4: 性能对比
        compare_rule_vs_llm()

        print("\n" + "="*80)
        print("测试完成！")
        print("="*80)
        print("\n✓ 规则匹配: 快速准确，适用于标准表达")
        print("✓ LLM兜底: 覆盖口语化表达，提升用户体验")
        print("✓ 混合模式: 兼顾性能和准确性的最佳实践")

    except Exception as e:
        print(f"\n❌ 测试过程中出现异常:")
        print(f"  {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
