# ChatFlowDSL: 聊天机器人流程定义语言

本项目是一个为构建智能对话机器人而设计的领域特定语言 (DSL) 及其解释器。它允许开发者和产品设计师使用简单直观的 YAML 语法来定义复杂的对话逻辑，并通过模块化的架构轻松扩展功能。

## 核心特性

- **声明式DSL**: 使用 YAML 文件定义对话流程，将业务逻辑与代码分离，易于理解和维护。
- **状态机驱动**: 对话流程由严格的状态机管理，保证了流程的连贯性和可预测性。
- **模块化架构**: 核心功能（解析、解释、动作执行、会话管理）被拆分为独立组件，高度解耦，易于扩展。
- **可扩展的动作库**: 可以轻松添加新的动作类型（如 API 调用、数据库查询），以增强机器人的能力。
- **多会话管理**: 内置会话管理器，能够为多用户提供独立的对话上下文。

## 项目结构

```
├── main.py                 # (暂未使用) 应用主入口
├── requirements.txt        # Python 依赖
├── config/
│   └── config.yaml         # 配置文件
├── dsl/
│   ├── dsl_parser.py       # DSL 解析器
│   ├── interpreter.py      # 状态机解释器
│   ├── flows/              # 核心业务流程目录
│   │   ├── pre_sales/
│   │   │   └── product_inquiry.yaml
│   │   ├── in_sales/
│   │   │   └── order_management.yaml
│   │   ├── after_sales/
│   │   │   ├── refund.yaml
│   │   │   └── invoice.yaml
│   │   ├── troubleshooting/
│   │   │   └── headset_troubleshooting.yaml
│   │   └── common/
│   │       └── chitchat.yaml
│   └── examples/
│       └── refund_zh.yaml  # (V1旧版) 示例脚本
├── core/
│   ├── action_executor.py  # 动作执行器
│   └── session_manager.py  # 会话管理器
├── cli/
│   └── cli_interface.py    # 命令行交互界面
└── tests/
    └── ...                 # 测试代码
```

## 快速开始

1.  **安装依赖:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **运行模拟对话:**
    项目当前的核心逻辑和测试入口位于 `dsl/interpreter.py`。你可以修改该文件底部加载的yaml文件路径，来体验不同的对话流程：
    ```bash
    python dsl/interpreter.py
    ```
