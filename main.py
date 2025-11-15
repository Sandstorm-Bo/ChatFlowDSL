import yaml

from core.chatbot import Chatbot
from cli.cli_interface import CliInterface

def main():
    """
    Application entry point.
    Initializes the chatbot and starts the command-line interface.
    """
    print("正在初始化机器人...")
    # Chatbot会自动扫描并加载 dsl/flows/ 目录下的所有流程
    chatbot = Chatbot()
    
    # 使用一个固定的 session_id 来模拟单个用户的持续对话
    session_id = "cli_user_session"
    
    cli = CliInterface(chatbot, session_id)
    cli.start_chat_loop()

if __name__ == "__main__":
    main()
