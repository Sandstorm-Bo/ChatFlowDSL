from rich.console import Console
from rich.prompt import Prompt

class CliInterface:
    def __init__(self, message_handler):
        self.console = Console()
        self.message_handler = message_handler

    def start(self):
        self.console.print("[bold green]欢迎使用 ChatFlowDSL 智能客服。[/bold green]")
        self.console.print("输入 'exit' 或 'quit' 退出程序。")
        
        while True:
            try:
                user_input = Prompt.ask("[bold cyan]You[/bold cyan]")

                if user_input.lower() in ['exit', 'quit']:
                    self.console.print("[yellow]感谢使用，再见！[/yellow]")
                    break
                
                response = self.message_handler(user_input)
                self.console.print(f"[bold magenta]Bot[/bold magenta]: {response}")

            except KeyboardInterrupt:
                self.console.print("\n[yellow]检测到中断，程序退出。[/yellow]")
                break
            except Exception as e:
                self.console.print(f"[bold red]发生错误: {e}[/bold red]")

def dummy_handler(message: str) -> str:
    """一个虚拟的消息处理器，用于测试"""
    return f"已收到您的消息: '{message}'"

if __name__ == '__main__':
    cli = CliInterface(message_handler=dummy_handler)
    cli.start()
