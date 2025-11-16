"""
ChatFlow DSL 客户端
实现基于TCP Socket的智能客服客户端
可同时启动多个客户端实例进行并发测试
"""

import socket
import json
import sys
import threading
import time


class ChatClient:
    """
    智能客服客户端

    功能：
    1. 连接到服务器
    2. 发送用户消息
    3. 接收服务器响应
    4. 提供命令行交互界面
    """

    def __init__(self, host='127.0.0.1', port=8888, client_name=None):
        """
        初始化客户端

        Args:
            host: 服务器地址
            port: 服务器端口
            client_name: 客户端名称（用于区分多个客户端）
        """
        self.host = host
        self.port = port
        self.client_name = client_name or f"Client-{id(self)}"
        self.socket = None
        self.connected = False
        self.session_id = None
        self.authenticated = False
        self.user_id = None
        self.username = None

    def connect(self):
        """连接到服务器"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True

            print(f"[{self.client_name}] 成功连接到服务器 {self.host}:{self.port}")

            # 接收欢迎消息
            welcome_msg = self._receive_message()
            if welcome_msg:
                print(f"[{self.client_name}] {welcome_msg.get('message', '')}")
                self.session_id = welcome_msg.get('session_id')

                # 检查是否需要登录
                if welcome_msg.get('require_auth', False):
                    # 执行登录或注册流程
                    if not self.login_or_register():
                        print(f"[{self.client_name}] 认证失败，断开连接")
                        self.disconnect()
                        return False

            return True

        except Exception as e:
            print(f"[{self.client_name}] 连接失败: {e}")
            self.connected = False
            return False

    def login_or_register(self):
        """
        登录或注册选择流程

        Returns:
            认证成功返回True，失败返回False
        """
        if not self.connected:
            print(f"[{self.client_name}] 未连接到服务器")
            return False

        while True:
            try:
                choice = input(f"[{self.client_name}] 请选择: (1)登录 (2)注册 (q)退出: ").strip()
            except EOFError:
                return False

            if choice == "1":
                return self.login()
            elif choice == "2":
                return self.register()
            elif choice.lower() == "q":
                return False
            else:
                print(f"[{self.client_name}] 无效选项，请重新输入")

    def login(self, username=None, password=None):
        """
        用户登录认证

        Args:
            username: 用户名（可选，如果为None则从命令行输入）
            password: 密码（可选，如果为None则从命令行输入）

        Returns:
            登录成功返回True，失败返回False
        """
        if not self.connected:
            print(f"[{self.client_name}] 未连接到服务器")
            return False

        # 如果没有提供凭证，从命令行获取
        max_attempts = 3
        for attempt in range(max_attempts):
            if username is None:
                try:
                    username = input(f"[{self.client_name}] 请输入用户名: ").strip()
                except EOFError:
                    return False

            if password is None:
                try:
                    import getpass
                    password = getpass.getpass(f"[{self.client_name}] 请输入密码: ")
                except (EOFError, Exception):
                    # 如果getpass失败，使用普通input
                    try:
                        password = input(f"[{self.client_name}] 请输入密码: ").strip()
                    except EOFError:
                        return False

            # 发送登录请求
            login_request = {
                "type": "login",
                "username": username,
                "password": password
            }

            try:
                data = json.dumps(login_request, ensure_ascii=False).encode('utf-8')
                self.socket.sendall(data)

                # 接收认证结果
                auth_result = self._receive_message()

                if auth_result and auth_result.get("type") == "auth_result":
                    if auth_result.get("success"):
                        # 登录成功
                        self.authenticated = True
                        self.user_id = auth_result.get("user_id")
                        self.username = auth_result.get("username")
                        print(f"[{self.client_name}] {auth_result.get('message')}")
                        return True
                    else:
                        # 登录失败
                        print(f"[{self.client_name}] {auth_result.get('message')}")
                        # 重置凭证以便重新输入
                        username = None
                        password = None

                        if attempt < max_attempts - 1:
                            print(f"[{self.client_name}] 请重试（剩余 {max_attempts - attempt - 1} 次机会）")
                        else:
                            print(f"[{self.client_name}] 登录失败次数过多")
                            return False
                else:
                    print(f"[{self.client_name}] 收到未知响应")
                    return False

            except Exception as e:
                print(f"[{self.client_name}] 登录失败: {e}")
                return False

        return False

    def register(self):
        """
        用户注册

        Returns:
            注册成功返回True，失败返回False
        """
        if not self.connected:
            print(f"[{self.client_name}] 未连接到服务器")
            return False

        try:
            # 收集注册信息
            username = input(f"[{self.client_name}] 请输入用户名: ").strip()
            if not username:
                print(f"[{self.client_name}] 用户名不能为空")
                return False

            import getpass
            try:
                password = getpass.getpass(f"[{self.client_name}] 请输入密码: ")
            except (EOFError, Exception):
                password = input(f"[{self.client_name}] 请输入密码: ").strip()

            if not password:
                print(f"[{self.client_name}] 密码不能为空")
                return False

            try:
                password_confirm = getpass.getpass(f"[{self.client_name}] 请再次输入密码: ")
            except (EOFError, Exception):
                password_confirm = input(f"[{self.client_name}] 请再次输入密码: ").strip()

            if password != password_confirm:
                print(f"[{self.client_name}] 两次输入的密码不一致")
                return False

            # 可选信息
            phone = input(f"[{self.client_name}] 请输入手机号（可选，直接回车跳过）: ").strip() or None
            email = input(f"[{self.client_name}] 请输入邮箱（可选，直接回车跳过）: ").strip() or None
            address = input(f"[{self.client_name}] 请输入地址（可选，直接回车跳过）: ").strip() or None

            # 发送注册请求
            register_request = {
                "type": "register",
                "username": username,
                "password": password,
                "phone": phone,
                "email": email,
                "address": address
            }

            data = json.dumps(register_request, ensure_ascii=False).encode('utf-8')
            self.socket.sendall(data)

            # 接收注册结果
            register_result = self._receive_message()

            if register_result and register_result.get("type") == "register_result":
                if register_result.get("success"):
                    # 注册成功，自动登录
                    self.authenticated = True
                    self.user_id = register_result.get("user_id")
                    self.username = register_result.get("username")
                    print(f"[{self.client_name}] {register_result.get('message')}")
                    return True
                else:
                    # 注册失败
                    print(f"[{self.client_name}] {register_result.get('message')}")
                    return False
            else:
                print(f"[{self.client_name}] 收到未知响应")
                return False

        except EOFError:
            return False
        except Exception as e:
            print(f"[{self.client_name}] 注册失败: {e}")
            return False

    def send_message(self, content):
        """
        发送消息到服务器

        Args:
            content: 消息内容

        Returns:
            服务器响应内容，失败返回None
        """
        if not self.connected:
            print(f"[{self.client_name}] 未连接到服务器")
            return None

        if not self.authenticated:
            print(f"[{self.client_name}] 未登录，请先登录")
            return None

        try:
            # 构造请求消息
            request = {
                "type": "message",
                "content": content
            }

            # 发送JSON消息
            data = json.dumps(request, ensure_ascii=False).encode('utf-8')
            self.socket.sendall(data)

            # 接收服务器响应
            response = self._receive_message()

            if response and response.get("type") == "response":
                return response.get("content")
            elif response and response.get("type") == "error":
                print(f"[{self.client_name}] 服务器错误: {response.get('message')}")
                return None
            else:
                print(f"[{self.client_name}] 收到未知响应: {response}")
                return None

        except Exception as e:
            print(f"[{self.client_name}] 发送消息失败: {e}")
            self.connected = False
            return None

    def _receive_message(self):
        """
        接收服务器消息

        Returns:
            消息字典，失败返回None
        """
        try:
            data = self.socket.recv(4096)
            if not data:
                return None

            message = json.loads(data.decode('utf-8'))
            return message

        except Exception as e:
            print(f"[{self.client_name}] 接收消息失败: {e}")
            return None

    def disconnect(self):
        """断开与服务器的连接"""
        if self.connected:
            try:
                # 发送退出消息
                exit_msg = {"type": "exit"}
                data = json.dumps(exit_msg).encode('utf-8')
                self.socket.sendall(data)
            except:
                pass

        if self.socket:
            try:
                self.socket.close()
            except:
                pass

        self.connected = False
        print(f"[{self.client_name}] 已断开连接")

    def start_interactive(self):
        """启动交互式命令行界面"""
        print("\n" + "=" * 60)
        print(f"{self.client_name} - 智能客服交互界面")
        print("=" * 60)
        print("提示：输入 'quit' 或 'exit' 退出")
        print("-" * 60)

        try:
            while self.connected:
                # 读取用户输入
                try:
                    user_input = input(f"\n[{self.client_name}] 您: ").strip()
                except EOFError:
                    break

                if not user_input:
                    continue

                # 检查退出命令
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print(f"[{self.client_name}] 再见！")
                    break

                # 发送消息并显示响应
                response = self.send_message(user_input)
                if response:
                    print(f"[{self.client_name}] 客服: {response}")
                else:
                    print(f"[{self.client_name}] 未收到响应，连接可能已断开")
                    break

        except KeyboardInterrupt:
            print(f"\n[{self.client_name}] 收到中断信号")

        finally:
            self.disconnect()


def run_single_client(client_id=1):
    """运行单个客户端实例"""
    client = ChatClient(client_name=f"Client-{client_id}")

    if client.connect():
        client.start_interactive()
    else:
        print(f"[Client-{client_id}] 无法连接到服务器")


def run_test_scenario(client_id, test_messages):
    """
    运行测试场景（用于自动化测试）

    Args:
        client_id: 客户端ID
        test_messages: 测试消息列表
    """
    client = ChatClient(client_name=f"TestClient-{client_id}")

    if not client.connect():
        print(f"[TestClient-{client_id}] 连接失败")
        return

    print(f"\n[TestClient-{client_id}] 开始测试场景")
    print("-" * 60)

    results = []
    for i, message in enumerate(test_messages, 1):
        print(f"\n[TestClient-{client_id}] 测试 {i}/{len(test_messages)}")
        print(f"[TestClient-{client_id}] 发送: {message}")

        response = client.send_message(message)

        if response:
            print(f"[TestClient-{client_id}] 收到: {response[:100]}...")
            results.append({"message": message, "response": response, "success": True})
        else:
            print(f"[TestClient-{client_id}] 无响应")
            results.append({"message": message, "response": None, "success": False})

        # 模拟真实用户操作间隔
        time.sleep(0.5)

    client.disconnect()

    print(f"\n[TestClient-{client_id}] 测试完成")
    print(f"[TestClient-{client_id}] 成功: {sum(1 for r in results if r['success'])}/{len(results)}")

    return results


def run_concurrent_test(num_clients=3):
    """
    运行并发测试（多个客户端同时发送请求）

    Args:
        num_clients: 并发客户端数量
    """
    print("\n" + "=" * 60)
    print(f"多线程并发测试 - {num_clients} 个客户端")
    print("=" * 60)

    # 定义测试场景
    test_scenarios = [
        ["我想买耳机", "有什么推荐的吗", "价格是多少"],
        ["查询订单", "ORD001", "退出"],
        ["我要退款", "订单号是ORD002", "取消"],
        ["发票申请", "ORD001", "不需要了"],
        ["你好", "今天天气怎么样", "再见"]
    ]

    threads = []
    results_list = []

    # 启动多个客户端线程
    for i in range(num_clients):
        scenario = test_scenarios[i % len(test_scenarios)]
        thread = threading.Thread(
            target=lambda cid, msgs: results_list.append(run_test_scenario(cid, msgs)),
            args=(i + 1, scenario)
        )
        threads.append(thread)
        thread.start()

        # 稍微错开启动时间
        time.sleep(0.2)

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    print("\n" + "=" * 60)
    print("并发测试完成")
    print("=" * 60)


def main():
    """客户端主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='ChatFlow DSL 客户端')
    parser.add_argument('--host', default='127.0.0.1', help='服务器地址')
    parser.add_argument('--port', type=int, default=8888, help='服务器端口')
    parser.add_argument('--id', type=int, default=1, help='客户端ID')
    parser.add_argument('--test', action='store_true', help='运行测试模式')
    parser.add_argument('--concurrent', type=int, default=0, help='并发测试客户端数量')

    args = parser.parse_args()

    if args.concurrent > 0:
        # 并发测试模式
        run_concurrent_test(args.concurrent)
    elif args.test:
        # 单客户端测试模式
        test_messages = [
            "我想买耳机",
            "有什么推荐的",
            "价格是多少",
            "我要最贵的",
            "退出"
        ]
        run_test_scenario(args.id, test_messages)
    else:
        # 交互模式
        run_single_client(args.id)


if __name__ == "__main__":
    main()
