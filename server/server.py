"""
ChatFlow DSL 服务器端
实现基于TCP Socket的多线程客服机器人服务器
支持多个客户端同时连接，每个客户端独立会话
"""

import socket
import threading
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.chatbot import Chatbot
from core.database_manager import DatabaseManager


class ChatServer:
    """
    多线程客服机器人服务器

    功能：
    1. 监听指定端口，接受客户端连接
    2. 为每个客户端创建独立线程处理请求
    3. 维护客户端会话状态
    4. 处理客户端消息并返回响应
    """

    def __init__(self, host='127.0.0.1', port=8888):
        """
        初始化服务器

        Args:
            host: 服务器监听地址
            port: 服务器监听端口
        """
        self.host = host
        self.port = port
        self.server_socket = None
        self.chatbot = Chatbot()
        self.db = DatabaseManager()  # 数据库管理器，用于用户认证
        self.running = False
        self.clients = {}  # 存储活跃的客户端连接 {session_id: (conn, addr)}
        self.authenticated_users = {}  # 存储已认证的用户 {session_id: user_id}
        self.clients_lock = threading.Lock()  # 保护客户端字典的线程锁

        print(f"[服务器] 初始化完成")
        print(f"[服务器] 已加载 {len(self.chatbot.flows)} 个业务流程")

    def start(self):
        """启动服务器，开始监听客户端连接"""
        try:
            # 创建TCP套接字
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # 设置端口复用（避免重启时端口被占用）
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # 绑定地址和端口
            self.server_socket.bind((self.host, self.port))
            # 开始监听，最大等待连接数为5
            self.server_socket.listen(5)
            self.running = True

            print(f"[服务器] 启动成功，监听 {self.host}:{self.port}")
            print(f"[服务器] 等待客户端连接...")
            print("-" * 60)

            # 主循环：接受客户端连接
            while self.running:
                try:
                    # 阻塞等待客户端连接
                    conn, addr = self.server_socket.accept()

                    # 为新客户端创建会话ID（使用地址和端口）
                    session_id = f"{addr[0]}:{addr[1]}"

                    print(f"[服务器] 新客户端连接: {session_id}")

                    # 保存客户端连接
                    with self.clients_lock:
                        self.clients[session_id] = (conn, addr)

                    # 为该客户端创建独立线程处理请求
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(conn, addr, session_id),
                        daemon=True  # 守护线程，主线程退出时自动结束
                    )
                    client_thread.start()

                    print(f"[服务器] 当前活跃客户端数: {len(self.clients)}")

                except Exception as e:
                    if self.running:  # 只在服务器运行时打印错误
                        print(f"[服务器错误] 接受连接失败: {e}")

        except Exception as e:
            print(f"[服务器错误] 启动失败: {e}")

        finally:
            self.stop()

    def handle_client(self, conn, addr, session_id):
        """
        处理单个客户端的请求（在独立线程中运行）

        Args:
            conn: 客户端socket连接
            addr: 客户端地址
            session_id: 会话ID
        """
        print(f"[线程-{session_id}] 开始处理客户端请求")

        try:
            # 发送欢迎消息
            welcome_msg = {
                "type": "welcome",
                "message": f"欢迎使用智能客服系统！请先登录。",
                "session_id": session_id,
                "require_auth": True
            }
            self._send_message(conn, welcome_msg)

            # 循环接收和处理客户端消息
            while self.running:
                try:
                    # 接收客户端消息（最大4096字节）
                    data = conn.recv(4096)

                    if not data:
                        # 客户端断开连接
                        print(f"[线程-{session_id}] 客户端断开连接")
                        break

                    # 解析JSON消息
                    try:
                        request = json.loads(data.decode('utf-8'))
                    except json.JSONDecodeError:
                        # 兼容纯文本消息
                        request = {"type": "message", "content": data.decode('utf-8').strip()}

                    print(f"[线程-{session_id}] 收到消息: {request.get('content', request)}")

                    # 处理不同类型的请求
                    if request.get("type") == "login":
                        # 处理登录请求
                        username = request.get("username", "")
                        password = request.get("password", "")

                        print(f"[线程-{session_id}] 登录尝试: username={username}")

                        # 验证用户凭证
                        user_data = self.db.authenticate_user(username, password)

                        if user_data:
                            # 认证成功
                            user_id = user_data["user_id"]
                            with self.clients_lock:
                                self.authenticated_users[session_id] = user_id

                            response = {
                                "type": "auth_result",
                                "success": True,
                                "user_id": user_id,
                                "username": user_data["username"],
                                "message": f"登录成功！欢迎您，{user_data['username']}！"
                            }
                            print(f"[线程-{session_id}] 用户 {username} 登录成功，user_id={user_id}")
                        else:
                            # 认证失败
                            response = {
                                "type": "auth_result",
                                "success": False,
                                "message": "用户名或密码错误，请重试。"
                            }
                            print(f"[线程-{session_id}] 用户 {username} 登录失败")

                        self._send_message(conn, response)

                    elif request.get("type") == "register":
                        # 处理注册请求
                        username = request.get("username", "")
                        password = request.get("password", "")
                        phone = request.get("phone")
                        email = request.get("email")
                        address = request.get("address")

                        print(f"[线程-{session_id}] 注册尝试: username={username}")

                        # 注册用户
                        result = self.db.register_user(username, password, phone, email, address)

                        if result["success"]:
                            # 注册成功，自动登录
                            user_id = result["user_id"]
                            with self.clients_lock:
                                self.authenticated_users[session_id] = user_id

                            response = {
                                "type": "register_result",
                                "success": True,
                                "user_id": user_id,
                                "username": username,
                                "message": result["message"]
                            }
                            print(f"[线程-{session_id}] 用户 {username} 注册成功，user_id={user_id}")
                        else:
                            # 注册失败
                            response = {
                                "type": "register_result",
                                "success": False,
                                "message": result["message"]
                            }
                            print(f"[线程-{session_id}] 用户 {username} 注册失败: {result['message']}")

                        self._send_message(conn, response)

                    elif request.get("type") == "message":
                        # 普通对话消息 - 需要先认证
                        user_id = self.authenticated_users.get(session_id)

                        if not user_id:
                            # 未认证，要求登录
                            response = {
                                "type": "error",
                                "message": "请先登录后再使用服务。"
                            }
                            self._send_message(conn, response)
                            continue

                        user_input = request.get("content", "")

                        # 调用聊天机器人处理消息，传入user_id
                        response_text = self.chatbot.handle_message(session_id, user_input, user_id=user_id)

                        # 构造响应消息
                        response = {
                            "type": "response",
                            "content": response_text,
                            "session_id": session_id
                        }

                        # 发送响应
                        self._send_message(conn, response)
                        print(f"[线程-{session_id}] 发送响应: {response_text[:50] if isinstance(response_text, str) else str(response_text)[:50]}...")

                    elif request.get("type") == "ping":
                        # 心跳检测
                        self._send_message(conn, {"type": "pong"})

                    elif request.get("type") == "exit":
                        # 客户端主动退出
                        print(f"[线程-{session_id}] 客户端请求退出")
                        break

                    else:
                        # 未知请求类型
                        error_msg = {
                            "type": "error",
                            "message": f"未知的请求类型: {request.get('type')}"
                        }
                        self._send_message(conn, error_msg)

                except Exception as e:
                    print(f"[线程-{session_id}] 处理消息时出错: {e}")
                    error_msg = {
                        "type": "error",
                        "message": f"服务器处理消息时出错: {str(e)}"
                    }
                    try:
                        self._send_message(conn, error_msg)
                    except:
                        break

        except Exception as e:
            print(f"[线程-{session_id}] 客户端处理线程异常: {e}")

        finally:
            # 清理客户端连接
            with self.clients_lock:
                if session_id in self.clients:
                    del self.clients[session_id]
                # 清理认证信息
                if session_id in self.authenticated_users:
                    user_id = self.authenticated_users[session_id]
                    del self.authenticated_users[session_id]
                    print(f"[线程-{session_id}] 用户 {user_id} 已注销")

            # 关闭连接
            try:
                conn.close()
            except:
                pass

            print(f"[线程-{session_id}] 连接已关闭，剩余活跃客户端: {len(self.clients)}")

    def _send_message(self, conn, message):
        """
        发送JSON消息到客户端

        Args:
            conn: 客户端连接
            message: 消息字典
        """
        try:
            data = json.dumps(message, ensure_ascii=False).encode('utf-8')
            conn.sendall(data)
        except Exception as e:
            print(f"[服务器] 发送消息失败: {e}")
            raise

    def stop(self):
        """停止服务器"""
        print("\n[服务器] 正在关闭...")
        self.running = False

        # 关闭所有客户端连接
        with self.clients_lock:
            for session_id, (conn, _) in list(self.clients.items()):
                try:
                    conn.close()
                except:
                    pass
            self.clients.clear()

        # 关闭服务器套接字
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

        print("[服务器] 已关闭")

    def get_stats(self):
        """获取服务器统计信息"""
        with self.clients_lock:
            return {
                "active_clients": len(self.clients),
                "clients": list(self.clients.keys())
            }


def main():
    """服务器主函数"""
    print("=" * 60)
    print("ChatFlow DSL 智能客服服务器")
    print("=" * 60)

    # 创建并启动服务器
    server = ChatServer(host='127.0.0.1', port=8888)

    try:
        server.start()
    except KeyboardInterrupt:
        print("\n[服务器] 收到中断信号")
        server.stop()


if __name__ == "__main__":
    main()
