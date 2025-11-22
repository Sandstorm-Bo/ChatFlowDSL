# ChatFlowDSL: 聊天机器人流程定义语言

ChatFlowDSL 是一个面向智能客服场景的领域特定语言 (DSL) 及其运行时系统，支持：
- 用 YAML 定义对话流程（状态机）
- 规则匹配 + LLM 语义理解的混合触发
- 基于 TCP 的多客户端并发对话
- 用户认证（用户名/密码 + 会话 + JWT）+ 数据库查询（订单、商品等）

## 核心特性

- **声明式 DSL**：使用 YAML 文件定义业务流程，将业务逻辑与代码解耦。
- **状态机驱动**：明确的状态 / 动作 / 转换模型，便于推理和测试。
- **混合匹配**：规则优先，LLM 兜底，兼顾性能与语义理解。
- **CS 架构**：独立的 `server` 与 `client`，支持多客户端并发。
- **数据库与认证**：内置 SQLite 模拟业务数据 + 用户登录认证。

## 目录概览

```
├── requirements.txt            # Python 依赖（pyyaml / openai / pytest / PyJWT）
├── config/
│   └── config.yaml             # 运行配置（LLM、模式等）
├── dsl/
│   ├── dsl_parser.py           # DSL 解析器
│   ├── interpreter.py          # 状态机解释器
│   └── flows/                  # 业务流程脚本
│       ├── pre_sales/
│       ├── in_sales/
│       ├── after_sales/
│       ├── troubleshooting/
│       └── common/             # 业务DSL脚本示例
├── core/
│   ├── chatbot.py              # 聊天机器人编排器（混合匹配入口）
│   ├── action_executor.py      # 动作执行器（API / DB / 回复等）
│   ├── session_manager.py      # 会话管理（多会话 & 线程安全）
│   ├── database_manager.py     # 业务数据访问（SQLite）
│   └── logger.py               # 日志（可选）
├── llm/
│   └── llm_responder.py        # LLM 调用封装
├── server/
│   └── server.py               # TCP 服务器（多线程）
├── client/
│   ├── client.py               # 交互式命令行客户端
│   └── gui_client.py           # （可选）GUI 客户端示例
├── docs/
│   ├── PROJECT_DOCUMENTATION.md  # 课程设计总文档（最新）
│   ├── DSL_SPECIFICATION.md      # DSL 语法规范
│   ├── HYBRID_MATCHING_GUIDE.md  # 混合匹配机制说明
│   ├── AUTHENTICATION_GUIDE.md   # 用户认证与 JWT 鉴权说明
│   └── IMPLEMENTATION_SUMMARY.md # 关键实现与改造总结
└── tests/
    ├── demo_authentication.py     # 认证流程演示脚本
    ├── demo_flow_switching.py     # 流程切换演示脚本
    ├── demo_hybrid_matching.py    # 混合匹配演示脚本
    ├── mocks.py                   # Mock LLM / Mock DB 测试桩
    ├── test_api_connection.py
    ├── test_authentication.py
    ├── test_chatbot_flows.py
    ├── test_colloquial_expressions.py
    ├── test_fixes_auto.py
    ├── test_integration.py
    ├── test_interpreter.py
    ├── test_server_llm.py
    └── test_with_mocks.py         # 其它单元 / 集成测试
```

## 快速开始

1. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

2. 配置运行模式
   - 在 `config/config.yaml` 中设置：
     - 仅规则模式（不依赖 LLM）：`mode: "rule"`
     - 混合匹配模式：`mode: "hybrid"` 并配置好 `llm.api_key`

3. 启动服务器 + 命令行客户端
   ```bash
   # 终端1：启动服务器
   python server/server.py

   # 终端2：启动客户端
   python client/client.py

   # optimal choice: 启动图形化客户端
   python client/gui_client.py
   ```

4. 混合匹配演示脚本（需要在 `config/config.yaml` 中配置 LLM）
   ```bash
   python tests/demo_hybrid_matching.py
   ```

更多课程设计与测试相关内容，请参考：
- `docs/PROJECT_DOCUMENTATION.md`
- `docs/TEST_REPORT.md`（测试用例与结果汇总）
