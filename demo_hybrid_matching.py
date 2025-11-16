"""
混合匹配机制演示脚本

展示"规则优先 + LLM兜底"的强大能力
"""

import sys
import yaml
from core.chatbot import Chatbot
from llm.llm_responder import LLMResponder


def print_banner(text):
    """打印美化的标题"""
    print(f"\n{'='*80}")
    print(f"  {text}")
    print(f"{'='*80}\n")


def demo_rule_matching():
    """演示1: 规则匹配（快速、精确）"""
    print_banner("演示1: 规则匹配 - 标准表达")

    chatbot = Chatbot(flows_dir="dsl/flows", llm_responder=None)

    test_cases = [
        "你好",
        "我想了解产品",
        "查询订单A1234567890",
        "我要退款",
    ]

    for user_input in test_cases:
        print(f"👤 用户: {user_input}")
        responses = chatbot.handle_message(f"demo-rule-{user_input[:5]}", user_input)
        print(f"🤖 系统: {responses[0] if responses else '(无回复)'}\n")


def demo_llm_fallback():
    """演示2: LLM兜底（理解口语化表达）"""
    print_banner("演示2: LLM兜底 - 口语化表达")

    # 加载配置
    try:
        with open("config/config.yaml", 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print("⚠️ 配置文件不存在: config/config.yaml")
        print("提示: 请先配置LLM API Key")
        return

    llm_config = config.get("llm", {})
    if not llm_config.get("api_key"):
        print("⚠️ 未配置LLM API Key")
        print("提示: 请在config/config.yaml中配置llm.api_key")
        return

    # 初始化LLM响应器
    llm_responder = LLMResponder(
        api_key=llm_config["api_key"],
        model_name=llm_config["model_name"],
        base_url=llm_config.get("base_url"),
        timeout=llm_config.get("timeout", 30)
    )

    chatbot = Chatbot(flows_dir="dsl/flows", llm_responder=llm_responder)

    # 口语化测试用例
    test_cases = [
        {
            "input": "那个单子发到哪了",
            "note": "口语化表达：'单子' = 订单"
        },
        {
            "input": "东西坏了想退",
            "note": "简化表达：想退款"
        },
        {
            "input": "帮我看看你们卖啥",
            "note": "口语化：'卖啥' = 有什么产品"
        },
    ]

    for case in test_cases:
        print(f"👤 用户: {case['input']}")
        print(f"   💡 {case['note']}")
        responses = chatbot.handle_message(f"demo-llm-{case['input'][:5]}", case["input"])
        print(f"🤖 系统: {responses[0] if responses else '(无回复)'}\n")


def demo_performance_comparison():
    """演示3: 性能对比"""
    print_banner("演示3: 性能对比 - 规则 vs LLM")

    import time

    # 纯规则匹配
    chatbot_rule = Chatbot(flows_dir="dsl/flows", llm_responder=None)

    test_input = "查询订单A1234567890"
    print(f"测试输入: {test_input}")

    start = time.time()
    chatbot_rule.handle_message("perf-test-rule", test_input)
    rule_time = (time.time() - start) * 1000

    print(f"\n✓ 规则匹配: {rule_time:.2f}ms")
    print(f"  - 优势: 极快响应")
    print(f"  - 适用: 标准表达")

    # 尝试LLM模式（如果配置了）
    try:
        with open("config/config.yaml", 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        llm_config = config.get("llm", {})
        if llm_config.get("api_key"):
            llm_responder = LLMResponder(
                api_key=llm_config["api_key"],
                model_name=llm_config["model_name"],
                base_url=llm_config.get("base_url"),
                timeout=llm_config.get("timeout", 30)
            )

            chatbot_hybrid = Chatbot(flows_dir="dsl/flows", llm_responder=llm_responder)

            llm_test_input = "那个单子到哪了"
            print(f"\n测试输入: {llm_test_input} (口语化)")

            start = time.time()
            chatbot_hybrid.handle_message("perf-test-llm", llm_test_input)
            llm_time = (time.time() - start) * 1000

            print(f"\n✓ LLM兜底: {llm_time:.2f}ms")
            print(f"  - 优势: 理解语义")
            print(f"  - 适用: 口语化表达")

            print(f"\n📊 性能差异: LLM耗时约为规则的 {(llm_time/rule_time):.1f}x")
        else:
            print("\n⚠️ 未配置LLM，跳过LLM性能测试")

    except Exception as e:
        print(f"\n⚠️ LLM测试失败: {str(e)}")


def interactive_demo():
    """演示4: 交互式体验"""
    print_banner("演示4: 交互式体验 - 自由对话")

    try:
        with open("config/config.yaml", 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except:
        config = {}

    llm_responder = None
    llm_config = config.get("llm", {})

    if llm_config.get("api_key"):
        llm_responder = LLMResponder(
            api_key=llm_config["api_key"],
            model_name=llm_config["model_name"],
            base_url=llm_config.get("base_url"),
            timeout=llm_config.get("timeout", 30)
        )
        print("✓ LLM响应器已启用（混合模式）")
    else:
        print("ℹ️ 仅使用规则匹配（无LLM）")

    chatbot = Chatbot(flows_dir="dsl/flows", llm_responder=llm_responder)
    session_id = "interactive-demo"

    print("\n您可以输入任何问题，系统会自动选择最佳匹配方式")
    print("输入 'quit' 或 'exit' 退出\n")

    while True:
        try:
            user_input = input("👤 您: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'bye', '退出']:
                print("\n👋 再见！")
                break

            responses = chatbot.handle_message(session_id, user_input)

            print(f"🤖 系统:")
            for response in responses:
                print(f"  {response}")
            print()

        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 错误: {str(e)}\n")


def main():
    """主函数"""
    print("\n")
    print("╔" + "═"*78 + "╗")
    print("║" + " "*22 + "ChatFlowDSL 混合匹配演示" + " "*23 + "║")
    print("║" + " "*78 + "║")
    print("║" + " "*18 + "规则优先 + LLM语义理解兜底" + " "*20 + "║")
    print("╚" + "═"*78 + "╝")

    print("\n请选择演示模式：")
    print("  1. 规则匹配演示（快速、精确）")
    print("  2. LLM兜底演示（口语化理解）")
    print("  3. 性能对比（规则 vs LLM）")
    print("  4. 交互式体验（自由对话）")
    print("  0. 运行所有演示")

    choice = input("\n请输入选项 (0-4): ").strip()

    if choice == "1":
        demo_rule_matching()
    elif choice == "2":
        demo_llm_fallback()
    elif choice == "3":
        demo_performance_comparison()
    elif choice == "4":
        interactive_demo()
    elif choice == "0":
        demo_rule_matching()
        demo_llm_fallback()
        demo_performance_comparison()
        print("\n是否进入交互式体验？(y/n): ", end="")
        if input().lower() == 'y':
            interactive_demo()
    else:
        print("无效选项")

    print("\n" + "="*80)
    print("  演示结束！")
    print("="*80)
    print("\n📚 更多文档:")
    print("  - 混合匹配指南: docs/HYBRID_MATCHING_GUIDE.md")
    print("  - DSL语法规范: docs/DSL_SPECIFICATION.md")
    print("  - 项目文档: docs/PROJECT_DOCUMENTATION.md")
    print()


if __name__ == "__main__":
    main()
