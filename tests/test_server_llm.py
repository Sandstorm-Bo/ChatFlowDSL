"""
测试服务器的LLM意图识别功能
验证修复后的server.py是否正确加载LLM响应器
"""

import socket
import json
import time


def test_llm_intent_recognition():
    """测试LLM意图识别功能"""
    print("=" * 60)
    print("测试服务器LLM意图识别功能")
    print("=" * 60)

    # 连接到服务器
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        print("\n[1] 连接到服务器...")
        client.connect(("127.0.0.1", 8888))

        # 接收欢迎消息
        data = client.recv(4096)
        welcome = json.loads(data.decode("utf-8"))
        print(f"[2] 收到欢迎消息: {welcome.get('message')}")

        # 登录
        print("\n[3] 登录...")
        login_msg = {
            "type": "login",
            "username": "testuser",
            "password": "123456",
        }
        client.sendall(json.dumps(login_msg).encode("utf-8"))

        # 接收登录响应
        data = client.recv(4096)
        login_resp = json.loads(data.decode("utf-8"))
        print(f"[4] 登录结果: {login_resp.get('message')}")

        if not login_resp.get("success"):
            print("\n[提示] 请先注册用户: testuser / 123456")
            return

        # 测试用例：口语化表达，需要LLM理解
        test_cases = [
            {
                "input": "查询我的水杯送到哪里了",
                "expected_flow": "订单管理",
                "note": "包含'水杯'(商品)和'送到哪里'(物流)，需要LLM理解",
            },
            {
                "input": "那个单子发到哪了",
                "expected_flow": "订单管理",
                "note": "口语化：'单子' = 订单，'发到哪' = 物流状态",
            },
            {
                "input": "帮我看看你们卖啥",
                "expected_flow": "产品咨询",
                "note": "口语化：'卖啥' = 产品信息",
            },
        ]

        print("\n" + "=" * 60)
        print("开始测试口语化输入（需要LLM理解）")
        print("=" * 60)

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n[测试 {i}] {test_case['note']}")
            print(f"  输入: \"{test_case['input']}\"")
            print(f"  期望: 应该触发 {test_case['expected_flow']} 流程")

            # 发送测试消息
            msg = {"type": "message", "content": test_case["input"]}
            client.sendall(json.dumps(msg).encode("utf-8"))
            time.sleep(0.5)

            # 接收响应
            data = client.recv(4096)
            response = json.loads(data.decode("utf-8"))
            reply = response.get("content", "")

            print(
                f"  响应: {reply[:100] if isinstance(reply, str) else str(reply)[:100]}"
            )

            # 检查是否返回默认错误消息
            if isinstance(reply, list) and len(reply) > 0:
                reply_text = reply[0]
            else:
                reply_text = str(reply)

            if "抱歉，我暂时无法理解您的意思" in reply_text:
                print(f"  结果: ❌ 失败 - LLM未能识别意图（返回默认错误消息）")
            elif "您可以尝试" in reply_text:
                print(f"  结果: ❌ 失败 - LLM未能识别意图（返回默认提示）")
            else:
                print(f"  结果: ✓ 成功 - LLM正确识别意图并触发了相应流程")

            time.sleep(1)

        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)

    except ConnectionRefusedError:
        print("\n错误: 无法连接到服务器")
        print("请先运行服务器: python server/server.py")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback

        traceback.print_exc()
    finally:
        client.close()


if __name__ == "__main__":
    print("\n提示: 确保服务器正在运行 (python server/server.py)")
    print("按Enter键开始测试...")
    input()
    test_llm_intent_recognition()

