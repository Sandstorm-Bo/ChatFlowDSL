# ChatFlowDSL 用户认证系统指南

## 目录

1. [系统概述](#系统概述)
2. [架构设计](#架构设计)
3. [功能特性](#功能特性)
4. [使用指南](#使用指南)
5. [技术实现](#技术实现)
6. [测试验证](#测试验证)
7. [常见问题](#常见问题)

---

## 系统概述

ChatFlowDSL 用户认证系统是一个完整的用户登录和身份验证解决方案，旨在解决以下核心问题：

### 解决的问题

**问题场景：**
- 用户询问："我的水杯什么时候发货？"
- 系统困惑：不知道是哪个用户发起的请求
- 无法自动查询：需要用户手动提供订单号

**解决方案：**
- ✅ 用户登录认证
- ✅ 服务器识别用户身份
- ✅ 自动查询用户特定数据
- ✅ 智能化个性化服务

---

## 架构设计

### 整体架构图

```
┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│    Client    │───1───>│    Server    │───2───>│   Database   │
│              │<──6────│              │<──3────│              │
└──────────────┘        └──────────────┘        └──────────────┘
       │                       │                        │
       │                       │                        │
    Login                  Validate                 Users
   Request                Credentials               Orders
                              │                        │
                              v                        v
                      ┌──────────────┐        ┌──────────────┐
                      │   Session    │───4───>│   Chatbot    │
                      │   Manager    │<──5────│              │
                      └──────────────┘        └──────────────┘
                              │
                         session_id
                          ──────>
                          user_id
```

### 认证流程

1. **连接建立**
   - 客户端连接服务器
   - 服务器分配 session_id
   - 服务器发送认证要求

2. **用户登录**
   - 客户端提示用户输入用户名/密码
   - 发送登录请求到服务器
   - 服务器验证凭证

3. **认证成功**
   - 服务器保存 session_id -> user_id 映射
   - 返回认证成功消息
   - 客户端保存 user_id

4. **消息通信**
   - 客户端发送消息时自动携带 user_id
   - 服务器验证用户已登录
   - 转发消息到 Chatbot，附带 user_id

5. **智能查询**
   - Chatbot 创建/更新 session，关联 user_id
   - ActionExecutor 执行时，从 session 中读取 user_id
   - 自动查询该用户的数据（订单、退款等）

---

## 功能特性

### 1. 数据库用户认证

**数据表结构：**

```sql
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    address TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_login TEXT
)
```

**核心方法：**

```python
# 用户认证
user_data = db.authenticate_user(username, password)
# 返回: {"user_id": "U001", "username": "张三", ...}
# 或: None (认证失败)

# 根据用户名查询
user = db.get_user_by_username(username)

# 获取用户信息
user = db.get_user(user_id)
```

**特性：**
- ✅ 密码验证
- ✅ 自动更新最后登录时间
- ✅ 返回用户信息（不含密码）
- ✅ 用户名唯一性约束

### 2. 服务器端认证处理

**消息协议：**

```json
// 登录请求
{
  "type": "login",
  "username": "张三",
  "password": "password123"
}

// 认证成功响应
{
  "type": "auth_result",
  "success": true,
  "user_id": "U001",
  "username": "张三",
  "message": "登录成功！欢迎您，张三！"
}

// 认证失败响应
{
  "type": "auth_result",
  "success": false,
  "message": "用户名或密码错误，请重试。"
}
```

**服务器核心逻辑：**

```python
class ChatServer:
    def __init__(self):
        self.authenticated_users = {}  # {session_id: user_id}
        self.db = DatabaseManager()

    def handle_client(self, conn, addr, session_id):
        # 发送欢迎消息，要求登录
        welcome_msg = {
            "type": "welcome",
            "message": "欢迎使用智能客服系统！请先登录。",
            "session_id": session_id,
            "require_auth": True
        }
        self._send_message(conn, welcome_msg)

        # 处理登录请求
        if request.get("type") == "login":
            username = request.get("username")
            password = request.get("password")
            user_data = self.db.authenticate_user(username, password)

            if user_data:
                # 认证成功，保存映射
                self.authenticated_users[session_id] = user_data["user_id"]
                # 返回成功响应
            else:
                # 认证失败

        # 处理普通消息
        elif request.get("type") == "message":
            user_id = self.authenticated_users.get(session_id)
            if not user_id:
                # 未登录，拒绝服务
            else:
                # 调用chatbot，传入user_id
                response = self.chatbot.handle_message(
                    session_id,
                    user_input,
                    user_id=user_id
                )
```

**特性：**
- ✅ 拦截未认证请求
- ✅ 验证用户凭证
- ✅ 保存 session -> user 映射
- ✅ 自动注销清理

### 3. 客户端登录流程

**登录方法：**

```python
class ChatClient:
    def __init__(self):
        self.authenticated = False
        self.user_id = None
        self.username = None

    def connect(self):
        # 接收欢迎消息
        welcome_msg = self._receive_message()

        # 检查是否需要登录
        if welcome_msg.get('require_auth'):
            if not self.login():
                # 登录失败，断开连接
                self.disconnect()
                return False

    def login(self, username=None, password=None):
        # 从命令行获取用户名和密码
        if not username:
            username = input("请输入用户名: ")
        if not password:
            password = getpass.getpass("请输入密码: ")

        # 发送登录请求
        login_request = {
            "type": "login",
            "username": username,
            "password": password
        }
        self.socket.sendall(json.dumps(login_request).encode())

        # 接收认证结果
        auth_result = self._receive_message()

        if auth_result.get("success"):
            self.authenticated = True
            self.user_id = auth_result.get("user_id")
            self.username = auth_result.get("username")
            return True
        else:
            return False
```

**特性：**
- ✅ 自动触发登录流程
- ✅ 最多 3 次登录尝试
- ✅ 使用 getpass 隐藏密码输入
- ✅ 保存用户身份信息

### 4. 会话用户关联

**Session 类增强：**

```python
class Session:
    def __init__(self, session_id: str, user_id: Optional[str] = None):
        self.session_id = session_id
        self.user_id = user_id  # 关联的用户ID
        self.current_state_id = None
        self.variables = {}
        self.last_user_input = None
        self.created_at = time.time()
        self.last_active = time.time()

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,  # 导出时包含user_id
            "current_state_id": self.current_state_id,
            "variables": self.variables,
            "last_user_input": self.last_user_input,
        }
```

**SessionManager 增强：**

```python
class SessionManager:
    def get_session(self, session_id: str, user_id: Optional[str] = None):
        with self._lock:
            if session_id not in self._sessions:
                # 创建新会话时关联user_id
                self._sessions[session_id] = Session(session_id, user_id)
            else:
                session = self._sessions[session_id]
                # 如果提供了user_id，更新会话的user_id
                if user_id and not session.user_id:
                    session.user_id = user_id
            return self._sessions[session_id]
```

**特性：**
- ✅ Session 包含 user_id 字段
- ✅ 创建会话时自动关联
- ✅ 支持后续更新 user_id
- ✅ 线程安全操作

### 5. Chatbot 用户感知

**handle_message 方法签名更新：**

```python
def handle_message(self,
                   session_id: str,
                   user_input: str,
                   user_id: Optional[str] = None) -> List[str]:
    """
    Args:
        session_id: 会话ID
        user_input: 用户输入
        user_id: 用户ID（可选，用于识别用户并进行个性化查询）
    """
    # 获取或创建会话，关联user_id
    session = self.session_manager.get_session(session_id, user_id)
    # ... 后续处理
```

**特性：**
- ✅ 接受 user_id 参数
- ✅ 自动关联到 session
- ✅ 向下传递到 ActionExecutor

### 6. 智能自动查询

**ActionExecutor 增强：**

```python
def _handle_database_query(self, endpoint, params, session):
    # 订单查询示例
    if path == "orders/list":
        # 优先从session中获取user_id（关键！）
        user_id = session.get("user_id")
        if not user_id:
            # 降级到参数或默认用户
            user_id = params.get("user_id", "U001")

        # 使用user_id查询该用户的订单
        return self.db.get_user_orders(user_id)
```

**自动查询流程：**

```
用户说："我的订单什么时候发货？"
    ↓
Chatbot 识别意图 → 触发订单查询流程
    ↓
ActionExecutor 执行 database://orders/list
    ↓
从 session.user_id 获取当前用户 (例如: U001)
    ↓
数据库查询: SELECT * FROM orders WHERE user_id = 'U001'
    ↓
返回该用户的所有订单 [Order1, Order2, ...]
    ↓
系统回复："您有2个订单：
  - A1234567890: 无线蓝牙耳机Pro [已发货]
  - C1122334455: 便携充电宝20000mAh [已付款]"
```

**特性：**
- ✅ 自动从 session 读取 user_id
- ✅ 无需用户提供订单号
- ✅ 智能化个性化查询
- ✅ 降级机制保证兼容性

---

## 使用指南

### 快速开始

#### 1. 启动服务器

```bash
cd f:\Sandstorm\code\ChatFlowDSL
python server/server.py
```

**输出：**
```
[服务器] 初始化完成
[服务器] 已加载 6 个业务流程
[服务器] 启动成功，监听 127.0.0.1:8888
[服务器] 等待客户端连接...
```

#### 2. 启动客户端

```bash
python client/client.py
```

**输出：**
```
[Client-1] 成功连接到服务器 127.0.0.1:8888
[Client-1] 欢迎使用智能客服系统！请先登录。
[Client-1] 请输入用户名: 张三
[Client-1] 请输入密码:
[Client-1] 登录成功！欢迎您，张三！

Client-1 - 智能客服交互界面
============================================================
提示：输入 'quit' 或 'exit' 退出
------------------------------------------------------------

[Client-1] 您: 你好
[Client-1] 客服: 您好！有什么可以为您效劳的吗？我可以帮您：
- 查询商品信息
- 查看订单状态
- 处理退款退货
- 申请发票
- 解决设备故障
```

### 测试用户

系统预置了以下测试用户：

| 用户名 | 密码 | user_id | 订单数 |
|--------|------|---------|--------|
| 张三 | password123 | U001 | 2 |
| 李四 | password456 | U002 | 1 |
| 王五 | password789 | U003 | 0 |

### 演示脚本

#### 运行认证演示

```bash
python demo_authentication.py
```

**功能演示：**
1. 数据库用户认证
2. 会话关联用户
3. 用户特定订单查询
4. 带用户认证的聊天机器人
5. 智能自动查询（核心功能）

---

## 技术实现

### 文件修改清单

#### 1. 数据库管理器 (`core/database_manager.py`)

**修改内容：**
- 增加 `users` 表的 `password` 和 `last_login` 字段
- 新增 `authenticate_user()` 方法：验证用户名密码
- 新增 `get_user_by_username()` 方法：根据用户名查询
- 更新测试数据，包含密码字段

**代码片段：**
```python
def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
    conn = self._get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, password)
    )
    row = cursor.fetchone()

    if row:
        user_data = dict(row)
        # 更新最后登录时间
        cursor.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = ?",
            (user_data["user_id"],)
        )
        conn.commit()
        # 移除密码字段
        user_data.pop("password", None)
        conn.close()
        return user_data

    conn.close()
    return None
```

#### 2. 服务器 (`server/server.py`)

**修改内容：**
- 导入 `DatabaseManager`
- 新增 `authenticated_users` 字典
- 修改欢迎消息，添加 `require_auth` 标志
- 新增登录请求处理逻辑
- 修改消息处理，验证用户已登录
- 调用 chatbot 时传入 `user_id`
- 断开连接时清理认证信息

**代码片段：**
```python
# 处理登录请求
if request.get("type") == "login":
    username = request.get("username", "")
    password = request.get("password", "")

    user_data = self.db.authenticate_user(username, password)

    if user_data:
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
    else:
        response = {
            "type": "auth_result",
            "success": False,
            "message": "用户名或密码错误，请重试。"
        }

    self._send_message(conn, response)
```

#### 3. 客户端 (`client/client.py`)

**修改内容：**
- 新增 `authenticated`、`user_id`、`username` 字段
- 新增 `login()` 方法
- 修改 `connect()` 方法，检查 `require_auth` 并自动登录
- 修改 `send_message()` 方法，验证已登录

**代码片段：**
```python
def login(self, username=None, password=None):
    max_attempts = 3
    for attempt in range(max_attempts):
        if username is None:
            username = input(f"[{self.client_name}] 请输入用户名: ").strip()

        if password is None:
            import getpass
            password = getpass.getpass(f"[{self.client_name}] 请输入密码: ")

        login_request = {
            "type": "login",
            "username": username,
            "password": password
        }

        self.socket.sendall(json.dumps(login_request).encode())
        auth_result = self._receive_message()

        if auth_result.get("success"):
            self.authenticated = True
            self.user_id = auth_result.get("user_id")
            self.username = auth_result.get("username")
            return True
        else:
            username = None
            password = None
            if attempt < max_attempts - 1:
                print(f"请重试（剩余 {max_attempts - attempt - 1} 次机会）")

    return False
```

#### 4. 会话管理器 (`core/session_manager.py`)

**修改内容：**
- `Session.__init__()` 增加 `user_id` 参数
- `Session.to_dict()` 包含 `user_id`
- `SessionManager.get_session()` 增加 `user_id` 参数，支持关联和更新

**代码片段：**
```python
class Session:
    def __init__(self, session_id: str, user_id: Optional[str] = None):
        self.session_id = session_id
        self.user_id = user_id  # 新增字段
        # ... 其他字段

def get_session(self, session_id: str, user_id: Optional[str] = None) -> Session:
    with self._lock:
        if session_id not in self._sessions:
            self._sessions[session_id] = Session(session_id, user_id)
        else:
            session = self._sessions[session_id]
            # 如果提供了user_id，更新会话
            if user_id and not session.user_id:
                session.user_id = user_id
        return self._sessions[session_id]
```

#### 5. 聊天机器人 (`core/chatbot.py`)

**修改内容：**
- `handle_message()` 增加 `user_id` 参数
- 调用 `session_manager.get_session()` 时传入 `user_id`

**代码片段：**
```python
def handle_message(self, session_id: str, user_input: str, user_id: Optional[str] = None) -> List[str]:
    """
    Args:
        session_id: 会话ID
        user_input: 用户输入
        user_id: 用户ID（可选，用于识别用户并进行个性化查询）
    """
    session = self.session_manager.get_session(session_id, user_id)
    # ... 后续处理
```

#### 6. 动作执行器 (`core/action_executor.py`)

**修改内容：**
- 修改 `database://orders/list` 查询逻辑
- 优先从 `session.user_id` 获取用户ID
- 降级到参数或默认值

**代码片段：**
```python
elif path == "orders/list":
    # 优先从session中获取user_id，实现自动查询当前用户的订单
    user_id = session.get("user_id")
    if not user_id:
        user_id = params.get("user_id", "U001")  # 降级到参数或默认用户
    return self.db.get_user_orders(user_id)
```

#### 7. 闲聊流程 (`dsl/flows/common/chitchat.yaml`)

**修改内容：**
- 增强 `state_start_chitchat` 的响应文本，提供功能菜单
- 为 `state_end_chitchat` 添加响应动作

**代码片段：**
```yaml
states:
  - id: "state_start_chitchat"
    actions:
      - type: respond
        text: "您好！有什么可以为您效劳的吗？我可以帮您：\n- 查询商品信息\n- 查看订单状态\n- 处理退款退货\n- 申请发票\n- 解决设备故障"
    transitions:
      - target: "state_end_chitchat"

  - id: "state_end_chitchat"
    actions:
      - type: respond
        text: "好的，请问您具体需要什么帮助？"
```

---

## 测试验证

### 单元测试

运行测试套件：

```bash
python tests/test_authentication.py
```

**测试覆盖：**
1. ✅ 数据库用户认证
   - 正确用户名密码 → 成功
   - 错误密码 → 失败
   - 不存在的用户 → 失败
2. ✅ 会话用户关联
   - 创建会话时关联 user_id
   - 会话字典包含 user_id
   - 动态更新 user_id
3. ✅ 用户特定数据查询
   - 不同用户获取各自订单
   - 订单属于正确的用户
4. ✅ Chatbot 用户感知
   - 接受 user_id 参数
   - 会话保留 user_id

### 集成测试

#### 测试场景 1: 完整登录流程

1. 启动服务器
2. 启动客户端
3. 输入用户名: `张三`
4. 输入密码: `password123`
5. 验证登录成功
6. 发送消息验证通信正常

#### 测试场景 2: 智能订单查询

```
用户: 张三 (U001)
输入: "我的订单什么时候发货"

预期响应:
您有2个订单：
- A1234567890: 无线蓝牙耳机Pro [已发货] 物流单号：SF1234567890
- C1122334455: 便携充电宝20000mAh [已付款] 待发货
```

#### 测试场景 3: 多用户隔离

```
客户端1: 登录为 张三 (U001)
客户端2: 登录为 李四 (U002)

客户端1 查询订单 → 返回 U001 的订单（2个）
客户端2 查询订单 → 返回 U002 的订单（1个）

验证：两个客户端的数据相互隔离
```

---

## 常见问题

### Q1: 如何添加新用户？

**方法 1: 直接操作数据库**

```python
from core.database_manager import DatabaseManager

db = DatabaseManager()
db.add_user({
    "user_id": "U004",
    "username": "赵六",
    "password": "mypassword",
    "phone": "13600136000",
    "email": "zhaoliu@example.com",
    "address": "深圳市南山区"
})
```

**方法 2: SQL 插入**

```sql
INSERT INTO users (user_id, username, password, phone, email, address)
VALUES ('U004', '赵六', 'mypassword', '13600136000', 'zhaoliu@example.com', '深圳市南山区');
```

### Q2: 如何修改用户密码？

```sql
UPDATE users SET password = 'new_password' WHERE user_id = 'U001';
```

### Q3: 登录失败次数过多怎么办？

客户端默认允许 3 次登录尝试。如果失败次数过多，客户端会断开连接。

**解决方案：**
- 重新启动客户端
- 确认用户名和密码正确
- 检查数据库中是否存在该用户

### Q4: 如何查看当前登录的用户？

**方法 1: 服务器日志**

服务器会打印登录信息：

```
[线程-127.0.0.1:12345] 用户 张三 登录成功，user_id=U001
```

**方法 2: 代码查询**

```python
# 在服务器端
session_id = "127.0.0.1:12345"
user_id = server.authenticated_users.get(session_id)
print(f"会话 {session_id} 的用户: {user_id}")
```

### Q5: 如何实现"记住密码"功能？

当前版本不支持自动登录。如需实现，可以：

1. 客户端保存用户名到配置文件
2. 每次启动时读取并预填充用户名
3. 用户只需输入密码

**示例代码：**

```python
import json

# 保存用户名
with open("client_config.json", "w") as f:
    json.dump({"last_username": "张三"}, f)

# 读取用户名
with open("client_config.json", "r") as f:
    config = json.load(f)
    default_username = config.get("last_username", "")
```

**注意：** 不建议保存密码到本地文件！

### Q6: 如何退出登录？

断开连接即退出登录：

```
输入: quit 或 exit
```

服务器会自动清理认证信息。

### Q7: 密码加密存储？

**当前实现：** 明文存储（仅用于演示）

**生产环境建议：** 使用哈希加密

```python
import hashlib

# 注册时加密密码
password_hash = hashlib.sha256(password.encode()).hexdigest()
db.add_user({"username": "user", "password": password_hash, ...})

# 登录时验证
input_hash = hashlib.sha256(input_password.encode()).hexdigest()
user = db.authenticate_user(username, input_hash)
```

**更安全的方案：** 使用 `bcrypt` 或 `argon2`

```python
import bcrypt

# 注册
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# 验证
if bcrypt.checkpw(input_password.encode(), password_hash):
    # 验证成功
```

### Q8: 如何实现 Token 认证？

当前使用 session_id 关联用户。如需 Token 认证：

1. 生成 JWT Token
2. 客户端保存 Token
3. 每次请求携带 Token
4. 服务器验证 Token

**示例：**

```python
import jwt
import datetime

# 服务器端生成 Token
token = jwt.encode({
    "user_id": "U001",
    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
}, "secret_key", algorithm="HS256")

# 客户端携带 Token
request = {
    "type": "message",
    "token": token,
    "content": "你好"
}

# 服务器端验证 Token
try:
    payload = jwt.decode(token, "secret_key", algorithms=["HS256"])
    user_id = payload["user_id"]
except jwt.ExpiredSignatureError:
    # Token 过期
except jwt.InvalidTokenError:
    # Token 无效
```

### Q9: 如何实现多设备登录？

**当前行为：** 同一用户可以在多个客户端同时登录（不同 session_id）

**如需限制单设备登录：**

```python
class ChatServer:
    def __init__(self):
        self.user_to_sessions = {}  # {user_id: [session_id1, session_id2]}

    def handle_login(self, session_id, user_id):
        # 检查用户是否已登录
        if user_id in self.user_to_sessions:
            # 踢出其他设备
            old_sessions = self.user_to_sessions[user_id]
            for old_session in old_sessions:
                self._send_message(
                    old_session,
                    {"type": "logout", "message": "您的账号在其他设备登录"}
                )

        # 记录新会话
        self.user_to_sessions[user_id] = [session_id]
```

### Q10: 性能优化建议？

1. **密码验证优化：** 使用哈希索引
2. **Session 缓存：** 使用 Redis 存储 session
3. **数据库连接池：** 复用数据库连接
4. **Token 过期：** 定期清理过期 session

---

## 附录

### A. 完整测试用户列表

| user_id | username | password | 订单数 | 备注 |
|---------|----------|----------|--------|------|
| U001 | 张三 | password123 | 2 | 有已发货和待发货订单 |
| U002 | 李四 | password456 | 1 | 有已送达订单 |
| U003 | 王五 | password789 | 0 | 新用户，无订单 |

### B. API 参考

#### 登录消息

```json
{
  "type": "login",
  "username": "string",
  "password": "string"
}
```

#### 认证结果

```json
{
  "type": "auth_result",
  "success": boolean,
  "user_id": "string",
  "username": "string",
  "message": "string"
}
```

#### 普通消息

```json
{
  "type": "message",
  "content": "string"
}
```

#### 系统响应

```json
{
  "type": "response",
  "content": "string" | ["string"],
  "session_id": "string"
}
```

### C. 数据库架构

**用户表 (users)**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| user_id | TEXT | PRIMARY KEY | 用户唯一标识 |
| username | TEXT | NOT NULL, UNIQUE | 用户名 |
| password | TEXT | NOT NULL | 密码 |
| phone | TEXT | | 手机号 |
| email | TEXT | | 邮箱 |
| address | TEXT | | 地址 |
| created_at | TEXT | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| last_login | TEXT | | 最后登录时间 |

**订单表 (orders)**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| order_id | TEXT | PRIMARY KEY | 订单号 |
| user_id | TEXT | FOREIGN KEY | 用户ID |
| product_id | TEXT | | 商品ID |
| product_name | TEXT | | 商品名称 |
| quantity | INTEGER | | 数量 |
| total_price | REAL | | 总价 |
| status | TEXT | | 状态 |
| shipping_address | TEXT | | 配送地址 |
| tracking_number | TEXT | | 物流单号 |
| created_at | TEXT | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TEXT | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

---

## 总结

ChatFlowDSL 用户认证系统提供了完整的登录认证解决方案，解决了以下核心问题：

✅ **用户身份识别**：服务器能够识别每个请求来自哪个用户

✅ **智能自动查询**：系统能够根据用户身份自动查询其订单、退款等数据

✅ **个性化服务**：不同用户获得不同的数据，实现真正的个性化客服

✅ **安全可靠**：用户名密码验证，session 隔离，数据安全

**下一步建议：**
- 密码加密存储 (bcrypt/argon2)
- Token 认证 (JWT)
- 多设备管理
- 密码重置功能
- 用户注册功能
- 权限管理系统

---

**文档版本：** 1.0
**最后更新：** 2025-01-20
**作者：** ChatFlowDSL Team
