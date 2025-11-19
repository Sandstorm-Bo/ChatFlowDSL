# ChatFlowDSL: 聊天机器人流程定义语言

ChatFlowDSL 是一个面向智能客服场景的领域特定语言 (DSL) 及其运行时系统，支持：
- 用 YAML 定义对话流程（状态机）
- 规则匹配 + LLM 语义理解的混合触发
- 基于 TCP 的多客户端并发对话
- 用户认证 + 数据库查询（订单、商品等）

## 核心特性

- **声明式 DSL**：使用 YAML 文件定义业务流程，将业务逻辑与代码解耦。
- **状态机驱动**：明确的状态 / 动作 / 转换模型，便于推理和测试。
- **混合匹配**：规则优先，LLM 兜底，兼顾性能与语义理解。
- **CS 架构**：独立的 `server` 与 `client`，支持多客户端并发。
- **数据库与认证**：内置 SQLite 模拟业务数据 + 用户登录认证。

## 目录概览

```
├── main.py                     # 辅助入口（可选）
├── requirements.txt            # Python 依赖
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
│       └── common/
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
│   └── client.py               # 交互式客户端
├── cli/
│   └── cli_interface.py        # 本地命令行体验入口
├── docs/
│   ├── PROJECT_DOCUMENTATION.md  # 课程设计总文档（最新）
│   ├── DSL_SPECIFICATION.md      # DSL 语法规范
│   ├── HYBRID_MATCHING_GUIDE.md  # 混合匹配机制说明
│   └── AUTHENTICATION_GUIDE.md   # 用户认证系统说明
└── tests/
    ├── test_api_connection.py
    ├── test_fixes_auto.py
    ├── test_server_llm.py
    └── tests/                   # 其它单元 / 集成测试
```

## 快速开始

1. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

2. 本地规则模式体验（不依赖 LLM）
   ```bash
   python cli/cli_interface.py
   ```

3. 启动服务器 + 客户端
   ```bash
   # 终端1：启动服务器
   python server/server.py

   # 终端2：启动客户端
   python client/client.py
   ```

4. 混合匹配演示脚本（需要在 `config/config.yaml` 中配置 LLM）
   ```bash
   python demo_hybrid_matching.py
   ```

更多课程设计相关内容，请参考 `docs/PROJECT_DOCUMENTATION.md`。
