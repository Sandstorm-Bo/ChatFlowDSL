from typing import List, Dict, Any, Optional
import re

# DSL解释器
class Interpreter:
    def __init__(self, rules: List[Dict[str, Any]]):
        self.rules = {rule['intent']: rule for rule in rules}

    def get_response(self, intent: str, user_input: str) -> Optional[str]:
        """
        根据意图和用户输入，匹配规则并返回响应。初始方案：re匹配
        """
        rule = self.rules.get(intent)
        
        if not rule:
            return "抱歉，我不太理解您的意思。"

        # 简单的正则匹配条件
        condition = rule.get('condition', {})
        match_pattern = condition.get('match')

        if match_pattern and re.search(match_pattern, user_input):
            return rule.get('response', {}).get('text')
        
        # 如果意图匹配但没有条件或条件不匹配，可以返回默认响应
        # 为简化，这里如果没有正则匹配，则认为不匹配
        if intent in self.rules and not match_pattern:
             return rule.get('response', {}).get('text')

        return "抱歉，无法在当前意图下匹配到合适的回答。"


if __name__ == '__main__':
    from dsl.dsl_parser import DslParser

    parser = DslParser('dsl/examples/refund_zh.yaml')
    rules = parser.get_rules()
    interpreter = Interpreter(rules)

    test_cases = [
        ("refund", "你好，我想退货，因为商品坏了"),
        ("inquiry", "帮我查一下物流"),
        ("refund", "这个怎么用？") 
    ]

    for intent, text in test_cases:
        response = interpreter.get_response(intent, text)
        print(f"意图: '{intent}', 输入: '{text}'\n  -> 响应: {response}\n")
