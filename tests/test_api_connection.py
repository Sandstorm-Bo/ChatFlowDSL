"""
API 连接测试工具
用于诊断 LLM API 连接问题
"""
import os
import sys
import yaml
import requests
import time

# 项目根目录
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT_DIR, "config", "config.yaml")


def load_config():
    """加载配置文件"""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_network():
    """测试网络连接"""
    print("\n" + "=" * 60)
    print("1. 网络连接测试")
    print("=" * 60)

    test_urls = [
        "https://api.siliconflow.cn",
    ]

    for url in test_urls:
        try:
            print(f"\n测试连接: {url}")
            start = time.time()
            response = requests.get(url, timeout=5)
            elapsed = time.time() - start
            print(
                f"  ✓ 成功! 状态码: {response.status_code}, 耗时: {elapsed:.2f}秒"
            )
        except Exception as e:
            print(f"  ✗ 失败! 错误: {str(e)}")


def test_api_endpoint():
    """测试 API 端点"""
    print("\n" + "=" * 60)
    print("2. API 端点测试")
    print("=" * 60)

    config = load_config()
    api_key = os.getenv("OPENAI_API_KEY", config["llm"]["api_key"])
    base_url = config["llm"]["base_url"]
    model = config["llm"]["model_name"]

    print(f"\n配置信息:")
    print(f"  Base URL: {base_url}")
    print(f"  Model: {model}")
    print(
        f"  API Key: {api_key[:15]}...{api_key[-5:] if len(api_key) > 20 else '(too short)'}"
    )

    # 测试 API 调用
    print(f"\n正在测试 API 调用...")

    try:
        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": model,
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 10,
        }

        print(f"  请求 URL: {url}")
        print(f"  请求头: Authorization: Bearer {api_key[:15]}...")
        print(f"  请求体: {data}")
        print(f"\n  发送请求中...")

        start = time.time()
        response = requests.post(url, json=data, headers=headers, timeout=10)
        elapsed = time.time() - start

        print(f"\n  响应状态码: {response.status_code}")
        print(f"  响应耗时: {elapsed:.2f}秒")
        print(f"  响应内容: {response.text[:500]}")

        if response.status_code == 200:
            print(f"\n  ✓ API 调用成功!")
        else:
            print(f"\n  ✗ API 调用失败!")

    except requests.exceptions.Timeout:
        print(f"  ✗ 请求超时!")
    except Exception as e:
        print(f"  ✗ 错误: {type(e).__name__}: {str(e)}")


def test_openai_client():
    """测试 OpenAI 客户端"""
    print("\n" + "=" * 60)
    print("3. OpenAI 客户端测试")
    print("=" * 60)

    try:
        from openai import OpenAI

        config = load_config()
        api_key = os.getenv("OPENAI_API_KEY", config["llm"]["api_key"])
        base_url = config["llm"]["base_url"]
        model = config["llm"]["model_name"]

        print(f"\n创建 OpenAI 客户端...")
        client = OpenAI(api_key=api_key, base_url=base_url, timeout=10.0)

        print(f"正在调用 API...")
        start = time.time()

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "hello"}],
            max_tokens=10,
        )

        elapsed = time.time() - start
        print(f"\n  ✓ 调用成功! 耗时: {elapsed:.2f}秒")
        print(f"  响应: {response.choices[0].message.content}")

    except Exception as e:
        print(f"\n  ✗ 调用失败!")
        print(f"  错误类型: {type(e).__name__}")
        print(f"  错误信息: {str(e)}")

        import traceback

        print(f"\n完整堆栈:")
        traceback.print_exc()


def main():
    print("\n" + "=" * 60)
    print("LLM API 连接诊断工具")
    print("=" * 60)

    # 检查环境变量
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"\n环境变量 OPENAI_API_KEY: {'已设置' if api_key else '未设置'}")
    if api_key:
        print(f"  值: {api_key[:15]}...{api_key[-5:]}")

    test_network()
    test_api_endpoint()
    test_openai_client()

    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)


if __name__ == "__main__":
    main()

