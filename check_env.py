"""检查环境变量"""
import os

api_key = os.getenv("OPENAI_API_KEY")

print("=" * 60)
print("环境变量检查")
print("=" * 60)
print(f"OPENAI_API_KEY: {api_key if api_key else '未设置'}")

if api_key:
    print(f"API Key 长度: {len(api_key)}")
    print(f"API Key 前缀: {api_key[:10]}..." if len(api_key) > 10 else api_key)
else:
    print("\n提示：")
    print("PowerShell: $env:OPENAI_API_KEY=\"your_key\"")
    print("CMD: set OPENAI_API_KEY=your_key")
    print("Linux/Mac: export OPENAI_API_KEY=your_key")
