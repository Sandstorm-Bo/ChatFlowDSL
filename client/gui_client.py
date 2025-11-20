import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from client import ChatClient


class ChatGUI:
    """
    基于 Tkinter 的图形化客户端：
    1. 启动后先展示登录界面（服务器地址 / 端口 / 用户名 / 密码）
    2. 登录成功后切换到聊天界面，以对话框形式与客服交互
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8888):
        self.root = tk.Tk()
        self.root.title("ChatFlowDSL 智能客服客户端")
        self.root.geometry("820x560")
        self.root.minsize(720, 480)

        # 统一使用 ttk 主题，稍微美化一下整体风格
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        default_font = ("Microsoft YaHei", 10)
        style.configure(".", font=default_font)

        # 允许窗口自适应
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        self.client: ChatClient | None = None

        # 登录界面变量
        self.host_var = tk.StringVar(value=host)
        self.port_var = tk.StringVar(value=str(port))
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.login_status_var = tk.StringVar(value="请先连接并登录服务器")
        self.register_status_var = tk.StringVar(value="")

        # 聊天界面控件占位
        self.chat_text: tk.Text | None = None
        self.input_var = tk.StringVar()
        self.send_button: ttk.Button | None = None

        self.login_frame: ttk.Frame | None = None
        self.chat_frame: ttk.Frame | None = None
        self.register_window: tk.Toplevel | None = None
        self._register_fields: dict[str, tk.StringVar] | None = None

        self._build_login_ui()

        # 关闭窗口时确保断开连接
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ==================== UI 构建 ====================
    def _build_login_ui(self):
        frame = ttk.Frame(self.root, padding=24)
        frame.grid(row=0, column=0, sticky="nsew")

        for i in range(6):
            frame.rowconfigure(i, weight=0)
        frame.rowconfigure(6, weight=1)
        frame.columnconfigure(1, weight=1)

        title_label = ttk.Label(
            frame,
            text="登录智能客服系统",
            font=("Microsoft YaHei", 14, "bold"),
        )
        title_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 16))

        ttk.Label(frame, text="服务器地址:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.host_var).grid(
            row=1, column=1, sticky="ew", pady=5
        )

        ttk.Label(frame, text="端口:").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.port_var).grid(
            row=2, column=1, sticky="ew", pady=5
        )

        ttk.Label(frame, text="用户名:").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.username_var).grid(
            row=3, column=1, sticky="ew", pady=5
        )

        ttk.Label(frame, text="密码:").grid(row=4, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.password_var, show="*").grid(
            row=4, column=1, sticky="ew", pady=5
        )

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=16, sticky="ew")
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)

        login_button = ttk.Button(btn_frame, text="连接并登录", command=self.on_login_clicked)
        login_button.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        register_button = ttk.Button(btn_frame, text="注册新用户", command=self.show_register_window)
        register_button.grid(row=0, column=1, sticky="ew")

        status_label = ttk.Label(
            frame, textvariable=self.login_status_var, foreground="#3367d6"
        )
        status_label.grid(row=6, column=0, columnspan=2, sticky="w", pady=5)

        self.login_frame = frame

    def _build_chat_ui(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.grid(row=0, column=0, sticky="nsew")

        frame.rowconfigure(0, weight=1)
        frame.rowconfigure(1, weight=0)
        frame.columnconfigure(0, weight=1)

        # 聊天记录区域
        text = tk.Text(
            frame,
            wrap="word",
            state="disabled",
            bg="#FFFFFF",
            font=("Microsoft YaHei", 10),
        )
        scrollbar = ttk.Scrollbar(frame, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)

        text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # 输入区域
        input_frame = ttk.Frame(frame)
        input_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        input_frame.columnconfigure(0, weight=1)

        entry = ttk.Entry(input_frame, textvariable=self.input_var)
        entry.grid(row=0, column=0, sticky="ew")
        entry.bind("<Return>", self.on_send)

        send_btn = ttk.Button(input_frame, text="发送", command=self.on_send)
        send_btn.grid(row=0, column=1, padx=(6, 0))

        self.chat_text = text
        # 配置不同角色的文本样式
        self.chat_text.tag_config("user", foreground="#1565C0")
        self.chat_text.tag_config("bot", foreground="#1B1B1B")
        self.chat_text.tag_config(
            "system", foreground="#757575", font=("Microsoft YaHei", 9, "italic")
        )
        self.send_button = send_btn
        self.chat_frame = frame

        # 欢迎提示
        self._append_system_message("登录成功，您可以开始和客服对话了。")

    # ==================== 事件处理 ====================
    def on_login_clicked(self):
        host = self.host_var.get().strip() or "127.0.0.1"
        port_str = self.port_var.get().strip() or "8888"
        username = self.username_var.get().strip()
        password = self.password_var.get()

        try:
            port = int(port_str)
        except ValueError:
            messagebox.showerror("错误", "端口必须是数字")
            return

        if not username or not password:
            messagebox.showwarning("提示", "请输入用户名和密码")
            return

        self.login_status_var.set("正在连接服务器并登录，请稍候...")

        def worker():
            try:
                client = ChatClient(host=host, port=port, client_name="GUI-Client")
                if not client.connect(auto_auth=False):
                    raise RuntimeError("连接服务器失败，请检查服务器是否已启动。")

                # 构造登录请求
                login_request = {
                    "type": "login",
                    "username": username,
                    "password": password,
                }
                data = json.dumps(login_request, ensure_ascii=False).encode("utf-8")
                client.socket.sendall(data)

                auth_result = client._receive_message()

                if (
                    not auth_result
                    or auth_result.get("type") != "auth_result"
                ):
                    raise RuntimeError("收到未知登录响应，请稍后重试。")

                if not auth_result.get("success"):
                    raise RuntimeError(auth_result.get("message", "用户名或密码错误"))

                # 登录成功，更新客户端状态
                client.authenticated = True
                client.user_id = auth_result.get("user_id")
                client.username = auth_result.get("username")

                self.client = client
                self.root.after(0, self._on_login_success)

            except Exception as e:
                msg = str(e) or "登录失败，请稍后重试。"
                self.root.after(0, lambda: self._on_login_failed(msg))

        threading.Thread(target=worker, daemon=True).start()

    def _on_login_success(self):
        self.login_status_var.set("登录成功")
        if self.login_frame is not None:
            self.login_frame.grid_forget()
        self._build_chat_ui()

    def _on_login_failed(self, message: str):
        self.login_status_var.set("登录失败")
        messagebox.showerror("登录失败", message)
        if self.client:
            try:
                self.client.disconnect()
            except Exception:
                pass
            self.client = None

    def on_send(self, event=None):
        content = self.input_var.get().strip()
        if not content:
            return

        if not self.client or not self.client.connected or not self.client.authenticated:
            messagebox.showwarning("提示", "尚未连接或登录成功")
            return

        # 将用户消息先写入聊天记录
        self._append_user_message(content)
        self.input_var.set("")

        # 在后台线程中发送消息并等待服务器响应，避免阻塞界面
        def worker(text_to_send: str):
            try:
                response = self.client.send_message(text_to_send)
                if response is None:
                    self.root.after(
                        0, lambda: self._append_system_message("未收到服务器响应，连接可能已断开。")
                    )
                    return

                # 服务器可能返回列表或字符串
                if isinstance(response, list):
                    reply_text = "\n".join(str(r) for r in response)
                else:
                    reply_text = str(response)

                self.root.after(0, lambda: self._append_bot_message(reply_text))
            except Exception as e:
                self.root.after(
                    0,
                    lambda: self._append_system_message(
                        f"发送消息失败：{type(e).__name__}: {e}"
                    ),
                )

        threading.Thread(target=worker, args=(content,), daemon=True).start()

    def on_close(self):
        if self.client:
            try:
                self.client.disconnect()
            except Exception:
                pass
        self.root.destroy()

    # ==================== 注册相关 ====================
    def show_register_window(self):
        if self.register_window and tk.Toplevel.winfo_exists(self.register_window):
            self.register_window.lift()
            return

        win = tk.Toplevel(self.root)
        win.title("注册新用户")
        win.geometry("420x360")
        win.transient(self.root)

        frame = ttk.Frame(win, padding=16)
        frame.pack(fill="both", expand=True)

        fields = {
            "username": tk.StringVar(),
            "password": tk.StringVar(),
            "confirm": tk.StringVar(),
            "phone": tk.StringVar(),
            "email": tk.StringVar(),
            "address": tk.StringVar(),
        }

        ttk.Label(frame, text="用户名:").grid(row=0, column=0, sticky="w", pady=6)
        ttk.Entry(frame, textvariable=fields["username"]).grid(row=0, column=1, sticky="ew", pady=6)

        ttk.Label(frame, text="密码:").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Entry(frame, textvariable=fields["password"], show="*").grid(row=1, column=1, sticky="ew", pady=6)

        ttk.Label(frame, text="确认密码:").grid(row=2, column=0, sticky="w", pady=6)
        ttk.Entry(frame, textvariable=fields["confirm"], show="*").grid(row=2, column=1, sticky="ew", pady=6)

        ttk.Label(frame, text="手机号 (可选):").grid(row=3, column=0, sticky="w", pady=6)
        ttk.Entry(frame, textvariable=fields["phone"]).grid(row=3, column=1, sticky="ew", pady=6)

        ttk.Label(frame, text="邮箱 (可选):").grid(row=4, column=0, sticky="w", pady=6)
        ttk.Entry(frame, textvariable=fields["email"]).grid(row=4, column=1, sticky="ew", pady=6)

        ttk.Label(frame, text="地址 (可选):").grid(row=5, column=0, sticky="w", pady=6)
        ttk.Entry(frame, textvariable=fields["address"]).grid(row=5, column=1, sticky="ew", pady=6)

        frame.columnconfigure(1, weight=1)

        status_label = ttk.Label(frame, textvariable=self.register_status_var, foreground="#3367d6")
        status_label.grid(row=6, column=0, columnspan=2, sticky="w", pady=4)

        button = ttk.Button(frame, text="提交注册", command=lambda: self.on_register_submit(fields))
        button.grid(row=7, column=0, columnspan=2, pady=12, sticky="ew")

        win.protocol("WM_DELETE_WINDOW", self._close_register_window)

        self.register_window = win
        self._register_fields = fields
        self.register_status_var.set("")

    def _close_register_window(self):
        if self.register_window:
            self.register_window.destroy()
        self.register_window = None
        self._register_fields = None
        self.register_status_var.set("")

    def on_register_submit(self, fields: dict[str, tk.StringVar]):
        host = self.host_var.get().strip() or "127.0.0.1"
        port_str = self.port_var.get().strip() or "8888"

        try:
            port = int(port_str)
        except ValueError:
            messagebox.showerror("错误", "端口必须是数字")
            return

        username = fields["username"].get().strip()
        password = fields["password"].get()
        confirm = fields["confirm"].get()
        phone = fields["phone"].get().strip() or None
        email = fields["email"].get().strip() or None
        address = fields["address"].get().strip() or None

        if not username or not password:
            messagebox.showwarning("提示", "用户名和密码不能为空")
            return
        if password != confirm:
            messagebox.showwarning("提示", "两次输入的密码不一致")
            return

        self.register_status_var.set("正在注册，请稍候...")

        def worker():
            try:
                client = ChatClient(host=host, port=port, client_name="GUI-Client")
                if not client.connect(auto_auth=False):
                    raise RuntimeError("无法连接服务器，请检查服务器是否已启动。")

                register_request = {
                    "type": "register",
                    "username": username,
                    "password": password,
                    "phone": phone,
                    "email": email,
                    "address": address,
                }
                data = json.dumps(register_request, ensure_ascii=False).encode("utf-8")
                client.socket.sendall(data)

                register_result = client._receive_message()
                if not register_result or register_result.get("type") != "register_result":
                    raise RuntimeError("收到未知注册响应，请稍后重试。")

                if not register_result.get("success"):
                    raise RuntimeError(register_result.get("message", "注册失败"))

                client.authenticated = True
                client.user_id = register_result.get("user_id")
                client.username = register_result.get("username")

                self.client = client
                self.root.after(0, self._on_register_success)

            except Exception as e:
                self.root.after(0, lambda: self._on_register_failed(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_register_success(self):
        self.register_status_var.set("注册成功，正在进入聊天界面...")
        self.login_status_var.set("注册并登录成功")
        self._close_register_window()
        self._on_login_success()

    def _on_register_failed(self, message: str):
        self.register_status_var.set("注册失败")
        messagebox.showerror("注册失败", message)
        if self.client:
            try:
                self.client.disconnect()
            except Exception:
                pass
            self.client = None

    # ==================== 文本输出工具 ====================
    def _append_message(self, text: str, tag: str):
        if not self.chat_text:
            return
        self.chat_text.configure(state="normal")
        self.chat_text.insert("end", text + "\n", tag)
        self.chat_text.insert("end", "\n")
        self.chat_text.see("end")
        self.chat_text.configure(state="disabled")

    def _append_user_message(self, text: str):
        self._append_message(f"您: {text}", "user")

    def _append_bot_message(self, text: str):
        self._append_message(f"客服: {text}", "bot")

    def _append_system_message(self, text: str):
        self._append_message(f"[系统] {text}", "system")

    # ==================== 入口 ====================
    def run(self):
        self.root.mainloop()


def main():
    gui = ChatGUI()
    gui.run()


if __name__ == "__main__":
    main()
