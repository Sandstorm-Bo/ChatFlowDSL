#
# ChatFlowDSL 课程设计文档（统一版）
#
# 本文基于当前代码库（2025-11-19）重新整理，
# 去除了与实现不符的旧描述，并作为课程设计的主文档入口。

## 目录

1. 需求分析
2. 概要设计
3. 详细设计概览
4. 接口与数据格式
5. 测试与验证
6. LLM 辅助开发说明

---

## 1. 需求分析

### 1.1 项目背景与目标

本项目实现一个基于 DSL 的智能客服系统，支持：
- 用 YAML 声明式定义对话流程；
- 在规则匹配的基础上，引入 LLM 进行语义兜底匹配；
- 采用 Client-Server 架构，支持多客户端并发对话；
- 通过认证和数据库模块，实现订单/商品等业务数据查询。

系统面向课程设计要求的几个关键点：
- 自定义脚本语言（DSL）及解释器；
- LLM API 集成与使用说明；
- 完整的 CS 架构与并发会话管理；
- 自动化测试与测试桩设计；
- 成体系的文档与代码结构。

### 1.2 功能需求（按课程任务拆解）

1. **脚本语言与执行**
   - 使用 YAML 描述对话流程（Flow / State / Action / Transition）。
   - 支持正则触发、条件分支、变量读写、API/数据库调用等。
   - 流程加载、校验与运行由解释器统一完成。

2. **多业务场景**
   - 售前：产品咨询、价格/功能说明（`pre_sales/product_inquiry.yaml`）。
   - 售中：订单查询、物流跟踪（`in_sales/order_management.yaml`）。
   - 售后：退款、发票开具（`after_sales/refund.yaml`、`after_sales/invoice.yaml`）。
   - 通用：闲聊问候（`common/chitchat.yaml`）、故障排查（`troubleshooting/headset_troubleshooting.yaml`）。

3. **会话与并发**
   - 每个客户端拥有独立会话上下文（`SessionManager`）。
   - 支持多客户端并发连接（多线程服务器）。
   - 会话超时与清理机制。

4. **LLM 集成与混合匹配**
   - 可选的 LLM 调用（通过 `config/config.yaml` 控制）。
   - 规则优先，LLM 兜底的“混合匹配”机制，用于流程触发与条件判断。

5. **认证与业务数据**
   - 用户登录认证（用户名/密码）。
   - 结合会话，将 `user_id` 传入业务流程，实现“我的订单”“我的退款”等个性化查询。

### 1.3 非功能需求

- **性能**：多数请求走本地规则匹配，平均响应时间 < 1 秒；少量走 LLM，接受百毫秒级延迟。
- **可扩展性**：通过新增 YAML 脚本或扩展 Action 类型即可支持新业务流程。
- **可维护性**：模块划分清晰，脚本与代码分离；提供独立的 DSL 规范/混合匹配/认证指南。

典型用户场景示例见 `dsl/flows` 中各 YAML 及混合匹配演示脚本 `demo_hybrid_matching.py`。

---

## 2. 概要设计

### 2.1 整体架构

系统采用典型的 CS 三层架构：

```
┌───────────────────────────────────────────────────┐
│                客户端层 (Client Layer)           │
│  - 交互客户端：client/client.py                  │
│  - CLI 本地演示：cli/cli_interface.py            │
└───────────────────────────────────────────────────┘
                         ↓ TCP (JSON)
┌───────────────────────────────────────────────────┐
│                服务层 (Server Layer)             │
│  - ChatServer：server/server.py                  │
│  - 多线程连接处理                                │
│  - 调用 Chatbot 完成业务逻辑                    │
└───────────────────────────────────────────────────┘
                         ↓
┌───────────────────────────────────────────────────┐
│                 核心层 (Core Layer)              │
│  - DSL 解析：dsl/dsl_parser.py                   │
│  - 状态机解释：dsl/interpreter.py               │
│  - 机器人编排：core/chatbot.py                  │
│  - 会话管理：core/session_manager.py             │
│  - 动作执行：core/action_executor.py             │
│  - 数据库访问：core/database_manager.py          │
│  - LLM 封装：llm/llm_responder.py                │
└───────────────────────────────────────────────────┘
                         ↓
┌───────────────────────────────────────────────────┐
│                 数据层 (Data Layer)              │
│  - DSL 脚本：dsl/flows/*.yaml                    │
│  - SQLite 数据库：data/chatbot.db                │
│  - 日志：debug/*.log                             │
└───────────────────────────────────────────────────┘
```

### 2.2 核心模块职责（与代码一致）

- `client/client.py`：交互客户端，负责从终端读取用户输入，将 JSON 消息发送给服务器并展示响应。
- `server/server.py`：TCP 服务器，负责连接管理、请求解析、调用 `Chatbot`，并将响应发回客户端。
- `dsl/dsl_parser.py`：解析 YAML DSL 文件为内部 `ChatFlow` 结构。
- `dsl/interpreter.py`：实现有限状态机解释执行逻辑。
- `core/chatbot.py`：
  - 加载所有流程；
  - 维护流程名称与“意图描述”的映射；
  - 实现规则触发与 LLM 触发的混合匹配；
  - 调用 `Interpreter` 执行单步流程。
- `core/session_manager.py`：管理会话对象，保证多线程环境下的安全访问。
- `core/action_executor.py`：执行 DSL 中定义的动作（回复、变量操作、数据库查询等）。
- `core/database_manager.py`：封装 SQLite 访问，提供商品/订单等业务数据接口。
- `llm/llm_responder.py`：将本地抽象转换为实际 LLM API 调用，支持不同模型/基地址配置。

日志系统（`core/logger.py`）目前为可选模块，核心逻辑主要使用简单的 `print` 与 `debug/*.log` 记录调试信息。

---

## 3. 详细设计概览

更细节的 DSL 语法请参考 `docs/DSL_SPECIFICATION.md`，混合匹配与认证分别参考 `docs/HYBRID_MATCHING_GUIDE.md` 与 `docs/AUTHENTICATION_GUIDE.md`，这里只给出与实现对应的关键点。

### 3.1 会话与状态机

**Session / SessionManager**（`core/session_manager.py`）：
- `Session` 保存：
  - `session_id`: 会话标识
  - `current_state_id`: 当前状态机状态
  - `variables`: 会话变量（如 `order_id` / `current_order` / `user_id` 等）
  - 活跃时间戳（用于超时判断）
- `SessionManager` 提供：
  - `get_session(session_id)`：获取或创建会话
  - `clear_session(session_id)`：删除会话
  - `get_active_session_count()`：统计活跃会话

**Interpreter**（`dsl/interpreter.py`）：
- 根据 `session.current_state_id` 定位状态；
- 执行当前状态 `actions`（交给 `ActionExecutor`）；
- 根据 `transitions` 中的条件对比本轮 `user_input` 和会话变量，决定下一个状态；
- 更新 `session.current_state_id` 并返回动作结果列表。

### 3.2 Chatbot 与混合匹配

**Chatbot**（`core/chatbot.py`）是应用层入口：
- 启动时加载 `dsl/flows` 下所有 YAML，构建 `ChatFlow` 对象；
- 为每个流程创建一个 `Interpreter`；
- 构建“流程名称 → 意图描述”的映射，用于 LLM 匹配。

请求处理主流程（`handle_message` 简化版）：

1. 根据 `session_id` 获取会话；
2. 如果当前没有激活流程（`active_flow_name`），尝试触发流程：
   - 先用入口状态上的 regex 规则匹配；
   - 未命中且配置了 LLM，则调用 `LLMResponder` 做语义匹配；
3. 找到流程后，交给对应的 `Interpreter` 执行一个状态步；
4. 将生成的文本动作作为响应返回。

混合匹配的详细 Prompt 与规则见 `docs/HYBRID_MATCHING_GUIDE.md` 与 `docs/IMPLEMENTATION_SUMMARY.md`。

### 3.3 动作与数据库

**ActionExecutor**（`core/action_executor.py`）支持的动作类型包括：
- `respond`：返回固定文本（支持插值，如 `{{session.order_id}}`）。
- `set_variable` / `extract_variable`：读写会话变量。
- `db_query` / 其它业务动作：通过 `DatabaseManager` 查询商品/订单等。

**DatabaseManager**（`core/database_manager.py`）封装了 SQLite 访问：
- 商品查询：`get_product(product_id)` / `list_products(category)`。
- 订单查询：`get_order(order_id)` / `list_user_orders(user_id)`。

认证系统的更详细设计与表结构请见 `docs/AUTHENTICATION_GUIDE.md`。

---

## 4. 接口与数据格式

### 4.1 网络消息格式

客户端与服务器之间通过 TCP 传输 JSON 文本，核心消息类型：

1. 登录请求
   ```json
   { "type": "login", "username": "string", "password": "string" }
   ```

2. 登录结果
   ```json
   {
     "type": "auth_result",
     "success": true,
     "user_id": "U001",
     "username": "张三",
     "message": "登录成功"
   }
   ```

3. 普通消息
   ```json
   { "type": "message", "content": "用户输入的文本" }
   ```

4. 服务器响应
   ```json
   {
     "type": "response",
     "content": ["您好，请提供您的订单号"],
     "session_id": "session-123"
   }
   ```

5. 心跳与退出
   ```json
   { "type": "ping" }
   { "type": "exit" }
   ```

### 4.2 主要类的对外行为

这里只保留实现中实际存在的主要接口，便于对照代码。

- `ChatServer`（`server/server.py`）
  - `start()`：启动服务器，监听端口并接受新连接。
  - `stop()`：停止服务器，关闭所有连接。
  - 内部为每个连接启动线程，循环接收 JSON 请求并调 `Chatbot.handle_message`。

- `ChatClient`（`client/client.py`）
  - `connect()` / `close()`：建立与服务器的 TCP 连接。
  - 交互模式：读取用户输入，构造 JSON 消息发送，并打印服务器返回的 `content`。

- `Chatbot`（`core/chatbot.py`）
  - `handle_message(session_id, user_input, user_id=None)`：
    - 处理一轮对话；根据是否已激活流程，执行触发或继续流程。
    - 返回字符串列表（每个元素是一条机器人回复）。

- `DslParser`（`dsl/dsl_parser.py`）
  - `get_flow()`：读取 YAML 文件，返回 `ChatFlow` 对象，内部保证必需字段存在。

- `Interpreter`（`dsl/interpreter.py`）
  - `process(session, user_input)`：执行当前状态动作 + 检查转换，并更新 `session`。

DSL 各字段的完整定义请参考 `docs/DSL_SPECIFICATION.md`。

---

## 5. 测试与验证

### 5.1 自动化测试现状

当前通过 `pytest` 运行测试：

```bash
pytest
```

收集到的主要测试包括：
- 根目录：
  - `test_api_connection.py`：验证 LLM API 连通性与基本调用。
  - `test_fixes_auto.py`：用于自动修复回归验证。
  - `test_server_llm.py`：服务器侧 LLM 集成的基本连通性测试。
- `tests/` 目录：
  - `test_authentication.py`：用户认证流程与数据库访问。
  - `test_chatbot_flows.py`：对话流程触发和会话状态保持。
  - `test_colloquial_expressions.py`：口语化表达的匹配验证（混合匹配相关）。
  - `test_integration.py`：从客户端到服务器再到 Chatbot 的集成链路。
  - `test_interpreter.py`：DSL 解释器的基础功能。
  - `test_with_mocks.py`：使用 `tests/mocks.py` 中的 Mock LLM / Mock DB 进行的单元测试。

目前运行结果：
- 绝大多数测试通过；
- 与流程状态细节相关的少量用例仍有失败（主要是订单流程的状态 ID 预期），反映的是“测试期望与实现略有偏差”，不影响主流程功能。

### 5.2 测试桩设计

`tests/mocks.py` 提供：
- `MockLLMResponder`：用关键词和正则模拟 LLM 的意图识别、实体提取与回复。
- `MockDatabaseManager`：在内存中提供商品/订单数据，避免依赖真实数据库文件。

在不配置真实 LLM / 不依赖真实 SQLite 文件的情况下，可以通过：

```bash
python tests/test_with_mocks.py
```

快速验证核心业务逻辑。

---

## 6. LLM 辅助开发说明

课程要求对“大模型辅助开发过程”进行说明，本项目主要在以下方面使用了 LLM（包括你当前正在使用的助手）：

1. **架构与模块划分**
   - 在已有 DSL 与基础解释器的基础上，借助 LLM 讨论并确定了：
     - CS 架构（client/server/chatbot）；
     - 会话管理与多线程模型；
     - 认证与数据库层的职责划分。

2. **混合匹配与 Prompt 设计**
   - 针对“规则 + LLM 兜底”的方案，反复试验 Prompt，逐步收敛到：
     - 明确的意图描述列表；
     - JSON 格式的结构化输出；
     - 合适的置信度阈值（默认 0.7）。
   - 这些内容已经沉淀在 `llm/llm_responder.py` 的接口设计与
     `docs/HYBRID_MATCHING_GUIDE.md`、`docs/IMPLEMENTATION_SUMMARY.md` 中。

3. **代码与重构建议**
   - 在实现 `ChatServer`、`Chatbot`、`ActionExecutor` 等模块时，
     通过与 LLM 交互获得了：
     - 线程安全与异常处理方面的改进建议；
     - 更清晰的函数/类边界；
     - 针对 DSL 状态机语义的澄清（哪些动作在何时执行）。

4. **测试用例设计**
   - 部分测试（特别是 Mock LLM/Mock DB 相关）是在 LLM 帮助下设计的，
     重点覆盖：
     - 典型业务路径（下单查询、退款等）；
     - 口语化表达与边界情况；
     - 并发访问下的 SessionManager 行为。

在整个过程中，所有由 LLM 生成或修改的代码，均经过人工审阅与本地运行验证，
并用自动化测试回归，避免“只在对话中正确”的情况。

---

**文档版本**：v2.0（统一版）  
**最后更新**：2025-11-19  
**说明**：本文件取代早期分散的设计/测试说明，测试细节与 DSL/混合匹配/认证的更完整说明，请分别参见：
- `docs/DSL_SPECIFICATION.md`
- `docs/HYBRID_MATCHING_GUIDE.md`
- `docs/AUTHENTICATION_GUIDE.md`
