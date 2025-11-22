# ChatFlowDSL 用户认证与 JWT 鉴权指南

## 1. 概述

本项目的认证系统分为两层：

- **用户名 / 密码登录**：基于 SQLite 用户表，完成账号认证；
- **会话 + JWT 鉴权**：服务器将认证后的用户信息同时绑定到会话（`session_id → user_id`）并签发一个可选的 JWT，客户端在后续请求中携带该 Token，用于无状态鉴权。

在不需要 JWT 的场景下，仅使用现有的会话认证即可；启用 JWT 后，系统同时支持“有状态会话 + 无状态 Token”双重机制。

---

## 2. 数据模型与存储

### 2.1 用户表结构

认证数据由 `core/database_manager.py` 管理，用户表（`users`）结构为：

```sql
CREATE TABLE users (
    user_id   TEXT PRIMARY KEY,
    username  TEXT NOT NULL UNIQUE,
    password  TEXT NOT NULL,
    phone     TEXT,
    email     TEXT,
    address   TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_login TEXT
);
```

当前实现中密码以明文形式存储在测试数据库中（便于课程演示），真实生产环境应替换为哈希存储（如 bcrypt / argon2）。

---

## 3. 登录与会话关联

### 3.1 登录消息与响应

客户端通过 `client/client.py` 发送登录请求：

```json
{ "type": "login", "username": "scb", "password": "123456" }
```

服务器 `ChatServer.handle_client` 在收到该请求后：

1. 调用 `DatabaseManager.authenticate_user(username, password)` 验证凭证；
2. 认证成功时，将 `session_id -> user_id` 记录到 `self.authenticated_users`；
3. 通过 `ChatServer._generate_jwt` 生成 JWT（见第 4 节）；
4. 返回登录结果：

```json
{
  "type": "auth_result",
  "success": true,
  "user_id": "U001",
  "username": "scb",
  "message": "登录成功！欢迎您，scb！",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  // 可选，JWT
}
```

客户端在 `ChatClient.login()` 中解析该响应：

- 将 `user_id`、`username` 保存在对象属性中；
- 如果响应中包含 `token` 字段，则保存到 `self.token`，后续请求自动携带。

---

## 4. JWT 鉴权设计

### 4.1 配置与密钥

JWT 相关配置写在 `config/config.yaml`：

```yaml
auth:
  jwt_secret: "dev-secret-change-me"  # 建议在生产环境改为随机字符串或用环境变量覆盖
  jwt_exp_hours: 24                   # Token 有效期（小时）
```

服务器初始化时（`ChatServer.__init__`）调用 `_init_jwt_config()`：

- 优先从环境变量 `CHATFLOW_JWT_SECRET` 读取密钥；
- 若未设置环境变量，则使用 `config.yaml` 中的 `auth.jwt_secret`；
- 若两者都未配置，则退回一个开发用默认值，并打印警告；
- 有效期默认为 24 小时，可通过 `jwt_exp_hours` 调整。

### 4.2 Token 生成

`ChatServer._generate_jwt(user_id, username)` 使用 `PyJWT` 生成 Token：

- 载荷字段：
  - `user_id`
  - `username`
  - `exp`：当前时间 + `jwt_exp_hours`
- 签名算法：`HS256`
- 密钥：`self.jwt_secret`

登录与注册成功时，都会尝试生成 Token 并在响应中附上 `"token"` 字段。

### 4.3 Token 验证

在处理普通消息时（`type == "message"`）：

1. 服务器从请求中读取 `token` 字段（如果存在）；
2. 调用 `_verify_jwt(token)`：
   - 使用相同的密钥和算法解码；
   - 若解码成功且未过期，返回 `(user_id, payload)`；
   - 若过期或无效，返回 `(None, None)` 并在服务器日志中打印原因。
3. 如果 `token` 有效，则优先采用其中的 `user_id`；
4. 如果没有 Token 或 Token 无效，则退回到旧的 `authenticated_users[session_id]` 映射；
5. 如果两种方式都无法获得 `user_id`，返回错误：

```json
{ "type": "error", "message": "请先登录后再使用服务。" }
```

---

## 5. 客户端如何使用 JWT

当前命令行客户端实现已经自动处理 JWT：  
在 `ChatClient.send_message()` 中，构造消息时会附加 `token` 字段（如果存在）：

```python
request = {
    "type": "message",
    "content": content,
}
if self.token:
    request["token"] = self.token
```

因此，对于终端用户来说，使用方式与原先完全一致：

1. 启动服务器：`python server/server.py`
2. 启动客户端并登录：`python client/client.py`
3. 登录成功后，客户端自动保存 Token 并在后续请求中附带，无需额外操作。

若将来新增 Web / 移动端客户端，也可以复用同样的 Token 字段，实现跨平台无状态认证。

---

## 6. 与会话管理的关系

- **会话（SessionManager）** 仍用于保存：
  - 每个 `session_id` 对应的状态机当前状态；
  - 会话变量（如 `order_id`、`current_order`、`refund_reason_type` 等）；
  - 当前关联的 `user_id`（便于在 DSL 中读取 `session.user_id`）。
- **JWT** 只负责传递用户身份与有效期，不直接管理状态机或会话变量。

这样设计的好处是：

- 在单机部署 / 课程演示时，可以主要依赖内存会话（简单可靠）；
- 在未来扩展到分布式或多实例部署时，可以逐步增加对 JWT 的依赖，减少对单节点内存状态的耦合。

---

## 7. 安全注意事项（课程层面）

当前实现为课程设计示例，重点在于展示“如何集成 JWT”，因此做了一些简化：

- 密钥默认为简单字符串，**请勿在真实生产环境中使用**；
- 密码目前为明文存储，真实环境应使用哈希；
- 未实现刷新 Token、黑名单、权限控制等高级特性。

如果在课程报告中说明此部分，可以强调：

- 已实现 JWT 的基本发放与验证流程；
- 已在客户端与服务器间通过 JSON 字段传递 Token；
- 有明确安全改进方向（密码哈希、密钥管理、Token 刷新等）。

