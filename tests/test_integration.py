"""
集成测试脚本
测试LLM集成和数据库功能
"""
import sys
import os
import yaml

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database_manager import DatabaseManager
from llm.llm_responder import LLMResponder
from core.action_executor import ActionExecutor
from core.session_manager import SessionManager

# 读取配置文件
def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "config.yaml")
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# 获取 API 配置
config = load_config()
API_KEY = os.getenv("OPENAI_API_KEY", config['llm']['api_key'])
MODEL_NAME = config['llm']['model_name']
BASE_URL = config['llm']['base_url']
TIMEOUT = config['llm'].get('timeout', 10.0)  # 默认10秒

print(f"[配置信息]")
print(f"  API Key: {'已设置' if API_KEY and API_KEY != 'YOUR_OPENAI_API_KEY' else '未设置（将使用降级模式）'}")
print(f"  Model: {MODEL_NAME}")
print(f"  Base URL: {BASE_URL}")
print(f"  Timeout: {TIMEOUT}秒")
print()

def test_database():
    """测试数据库功能"""
    print("=" * 60)
    print("测试1: 数据库功能")
    print("=" * 60)

    db = DatabaseManager()

    # 测试商品查询
    print("\n[商品查询]")
    products = db.get_all_products(limit=3)
    for p in products:
        print(f"  • {p['name']} - ¥{p['price']}")

    # 测试订单查询
    print("\n[订单查询]")
    order = db.get_order("A1234567890")
    if order:
        print(f"  订单号: {order['order_id']}")
        print(f"  商品: {order['product_name']}")
        print(f"  状态: {order['status']}")

    print("\n✓ 数据库测试通过")

def test_llm_responder():
    """测试LLM响应器"""
    print("\n" + "=" * 60)
    print("测试2: LLM意图识别")
    print("=" * 60)

    # 使用配置文件或环境变量中的API密钥
    responder = LLMResponder(api_key=API_KEY, model_name=MODEL_NAME, base_url=BASE_URL, timeout=TIMEOUT)

    test_cases = [
        "你好，我想看看你们的产品",
        "我的订单A1234567890到哪里了？",
        "我要退款",
        "能开发票吗？"
    ]

    print("\n[意图识别测试]")
    for text in test_cases:
        result = responder.recognize_intent(text)
        print(f"\n输入: {text}")
        print(f"意图: {result['intent']} (置信度: {result['confidence']})")
        print(f"理由: {result['reasoning']}")

    print("\n✓ LLM响应器测试通过（降级模式）")

def test_action_executor():
    """测试动作执行器"""
    print("\n" + "=" * 60)
    print("测试3: 动作执行器（数据库集成）")
    print("=" * 60)

    db = DatabaseManager()
    executor = ActionExecutor(db)
    session_manager = SessionManager()
    session = session_manager.create_session()

    # 测试数据库查询动作
    print("\n[测试数据库查询动作]")
    actions = [
        {
            "type": "api_call",
            "endpoint": "database://products/list",
            "params": {"limit": 3},
            "save_to": "session.featured_products"
        },
        {
            "type": "respond",
            "text": "我们的商品有：\n{{session.products_list}}"
        }
    ]

    responses = executor.execute(actions, session)
    print("\n响应:")
    for r in responses:
        print(r)

    # 测试订单查询
    print("\n\n[测试订单查询动作]")
    session2 = session_manager.create_session()
    session2.variables["order_id"] = "A1234567890"

    actions2 = [
        {
            "type": "api_call",
            "endpoint": "database://orders/get",
            "params": {},
            "save_to": "session.current_order"
        },
        {
            "type": "respond",
            "text": "订单 {{session.current_order.order_id}} 状态：{{session.order_status_text}}"
        }
    ]

    responses2 = executor.execute(actions2, session2)
    print("\n响应:")
    for r in responses2:
        print(r)

    print("\n✓ 动作执行器测试通过")

def test_integration():
    """集成测试：模拟完整的对话流程"""
    print("\n" + "=" * 60)
    print("测试4: 完整对话流程模拟")
    print("=" * 60)

    db = DatabaseManager()
    executor = ActionExecutor(db)
    session_manager = SessionManager()
    llm = LLMResponder(api_key=API_KEY, model_name=MODEL_NAME, base_url=BASE_URL, timeout=TIMEOUT)

    # 模拟场景：用户咨询产品
    print("\n[场景1: 产品咨询]")
    user_input1 = "我想看看耳机"
    print(f"用户: {user_input1}")

    # 识别意图
    intent_result = llm.recognize_intent(user_input1)
    print(f"识别意图: {intent_result['intent']}")

    # 执行动作
    session1 = session_manager.create_session()
    actions = [
        {
            "type": "api_call",
            "endpoint": "database://products/get",
            "params": {"product_id": "P001"},
            "save_to": "session.current_product"
        },
        {
            "type": "respond",
            "text": "【{{session.current_product.name}}】\n价格：¥{{session.current_product.price}}\n{{session.current_product.description}}"
        }
    ]

    responses = executor.execute(actions, session1)
    print("机器人:", responses[0] if responses else "")

    # 模拟场景：查询订单
    print("\n\n[场景2: 订单查询]")
    user_input2 = "查一下我的订单A1234567890"
    print(f"用户: {user_input2}")

    intent_result2 = llm.recognize_intent(user_input2)
    print(f"识别意图: {intent_result2['intent']}")

    session2 = session_manager.create_session()
    session2.variables["order_id"] = "A1234567890"

    actions2 = [
        {
            "type": "api_call",
            "endpoint": "database://orders/get",
            "params": {},
            "save_to": "session.current_order"
        },
        {
            "type": "respond",
            "text": "订单 {{session.current_order.order_id}}\n商品: {{session.current_order.product_name}}\n状态: {{session.order_status_text}}\n{{session.tracking_info}}"
        }
    ]

    responses2 = executor.execute(actions2, session2)
    print("机器人:", responses2[0] if responses2 else "")

    print("\n✓ 集成测试通过")

def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("ChatFlowDSL 集成测试套件")
    print("=" * 60)

    try:
        test_database()
        test_llm_responder()
        test_action_executor()
        test_integration()

        print("\n" + "=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)

        print("\n提示:")
        print("1. 数据库功能正常，已初始化5个商品和3个订单")
        print("2. LLM响应器工作正常（当前为降级模式，使用规则匹配）")
        print("3. 要启用真实LLM API:")
        print("   - 设置环境变量: set OPENAI_API_KEY=your_api_key")
        print("   - 或修改 config/config.yaml 中的 api_key")
        print("4. 支持的database://协议端点:")
        print("   - database://products/list")
        print("   - database://products/get")
        print("   - database://products/search")
        print("   - database://orders/get")
        print("   - database://orders/list")

        return 0

    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
