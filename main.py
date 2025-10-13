import yaml

from dsl.dsl_parser import DslParser
from dsl.interpreter import Interpreter
from llm.llm_responder import LLMResponder
from cli.cli_interface import CliInterface

class ChatFlow:
    def __init__(self, config_path="config/config.yaml"):
        self._load_config(config_path)
        
        self.dsl_parser = DslParser(file_path="dsl/examples/refund_zh.yaml")
        self.interpreter = Interpreter(rules=self.dsl_parser.get_rules())
        self.llm_responder = LLMResponder(
            api_key=self.config.get('llm', {}).get('api_key'),
            model_name=self.config.get('llm', {}).get('model_name')
        )
        self.cli = CliInterface(message_handler=self.handle_message)

    def _load_config(self, config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            print(f"配置文件 {config_path} 未找到，将使用默认设置。")
            self.config = {}

    def handle_message(self, user_input: str) -> str:
        """
        处理用户消息的核心逻辑。
        """
        intent = self.llm_responder.recognize_intent(user_input)
        response = self.interpreter.get_response(intent, user_input)
        
        return response

    def run(self):
        self.cli.start()

if __name__ == "__main__":
    app = ChatFlow()
    app.run()
