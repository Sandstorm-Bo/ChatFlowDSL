import pytest
from dsl.interpreter import Interpreter

def test_placeholder():
    """
    一个占位测试，确保pytest可以正常运行。
    """
    assert True

# TODO: 编写更详细的测试用例
# def test_get_response_with_matching_rule():
#     rules = [
#         {"intent": "greeting", "response": {"text": "Hello!"}}
#     ]
#     interpreter = Interpreter(rules)
#     response = interpreter.get_response("greeting", "Hi")
#     assert response == "Hello!"
