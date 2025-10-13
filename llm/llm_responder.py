from typing import Dict, Any

## LLM意图识别器
class LLMResponder:
    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name

    def recognize_intent(self, user_input: str) -> str:
        # TODO: 调用API完成
        print(f"--- (模拟LLM) 正在识别输入: '{user_input}' ---")
        
        if "退款" in user_input or "退货" in user_input:
            return "refund"
        elif "查" in user_input or "物流" in user_input:
            return "inquiry"
        else:
            return "unknown"

if __name__ == '__main__':
    # 示例用法
    responder = LLMResponder(api_key="test_key", model_name="test_model")
    
    test_inputs = ["你好，我想退款", "我的快递到哪了？", "今天天气怎么样"]
    for text in test_inputs:
        intent = responder.recognize_intent(text)
        print(f"用户输入: '{text}', 识别意图: '{intent}'\n")
