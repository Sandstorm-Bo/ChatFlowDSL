import sys
sys.path.append('.')

from core.chatbot import Chatbot

class CliInterface:
    def __init__(self, chatbot: Chatbot, session_id: str):
        """
        Initializes the CLI with a chatbot instance and a session ID.
        """
        self.chatbot = chatbot
        self.session_id = session_id

    def start_chat_loop(self):
        """
        Starts the main loop to read user input and print bot responses.
        """
        print("\n欢迎使用 ChatFlowDSL 机器人！输入 '退出' 来结束对话。")
        while True:
            try:
                user_input = input("您: ")
                if user_input.strip().lower() in ["退出", "exit", "quit"]:
                    print("机器人: 感谢您的使用，再见！")
                    break
                
                if not user_input.strip():
                    continue

                responses = self.chatbot.handle_message(self.session_id, user_input)
                
                for response in responses:
                    print(f"机器人: {response}")

            except (KeyboardInterrupt, EOFError):
                print("\n机器人: 对话已中断，再见！")
                break
