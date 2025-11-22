# ChatFlow DSL 脚本语言规范

**版本**: 1.0
**日期**: 2025-11-16
**作者**: ChatFlowDSL项目组

---

## 目录

1. [概述](#1-概述)
2. [文法定义（BNF范式）](#2-文法定义bnf范式)
3. [语法元素详解](#3-语法元素详解)
4. [数据类型](#4-数据类型)
5. [内置动作类型](#5-内置动作类型)
6. [条件匹配规则](#6-条件匹配规则)
7. [变量系统](#7-变量系统)
8. [完整示例](#8-完整示例)
9. [最佳实践](#9-最佳实践)
10. [常见错误](#10-常见错误)

---

## 1. 概述

ChatFlow DSL（Domain-Specific Language）是一种声明式脚本语言，用于定义智能客服机器人的对话流程。基于YAML格式，采用状态机模型，通过触发器、动作和状态转换来描述复杂的业务逻辑。

### 1.1 设计理念

- **声明式**: 描述"是什么"而非"怎么做"
- **状态驱动**: 基于有限状态机理论
- **易于理解**: 非技术人员也能快速上手
- **可扩展**: 支持自定义动作和条件

### 1.2 核心概念

| 概念 | 说明 | 示例 |
|------|------|------|
| **Flow** | 流程 | 产品咨询流程、订单管理流程 |
| **State** | 状态 | state_start, state_collect_info |
| **Trigger** | 触发器 | 用户输入匹配规则 |
| **Action** | 动作 | respond（回复）、api_call（API调用） |
| **Transition** | 转换 | 从一个状态到另一个状态 |
| **Session** | 会话 | 用户对话的上下文环境 |

---

## 2. 文法定义（BNF范式）

### 2.1 总体结构

```bnf
<flow> ::= <metadata> <states>

<metadata> ::= "name:" <string>
               "entry_point:" <state_id>
               ["description:" <string>]

<states> ::= "states:" <state_list>

<state_list> ::= <state> | <state> <state_list>
```

### 2.2 状态定义

```bnf
<state> ::= "- id:" <state_id>
            ["triggers:" <trigger_list>]
            ["actions:" <action_list>]
            ["transitions:" <transition_list>]

<state_id> ::= <identifier>

<identifier> ::= [a-zA-Z_][a-zA-Z0-9_]*
```

### 2.3 触发器

```bnf
<trigger_list> ::= <trigger> | <trigger> <trigger_list>

<trigger> ::= "- type:" <trigger_type>
              "value:" <pattern>

<trigger_type> ::= "regex" | "keyword" | "intent"

<pattern> ::= <regex_pattern> | <string>
```

### 2.4 动作

```bnf
<action_list> ::= <action> | <action> <action_list>

<action> ::= <respond_action> | <api_call_action> |
             <extract_variable_action> | <set_variable_action> |
             <wait_for_input_action>

<respond_action> ::= "- type: respond"
                     "text:" <string>

<api_call_action> ::= "- type: api_call"
                      "endpoint:" <uri>
                      ["params:" <params>]
                      ["save_to:" <variable>]

<extract_variable_action> ::= "- type: extract_variable"
                              "regex:" <regex_pattern>
                              "save_to:" <variable>

<set_variable_action> ::= "- type: set_variable"
                          "scope:" "session"
                          "key:" <identifier>
                          "value:" <value>

<wait_for_input_action> ::= "- type: wait_for_input"
```

### 2.5 转换

```bnf
<transition_list> ::= <transition> | <transition> <transition_list>

<transition> ::= "- condition:" <condition>
                 "target:" <state_id>

<condition> ::= <all_condition> | <any_condition> | <single_rule>

<all_condition> ::= "all:" <rule_list>

<any_condition> ::= "any:" <rule_list>

<rule_list> ::= <rule> | <rule> <rule_list>

<rule> ::= <regex_rule> | <variable_equals_rule> | <variable_exists_rule>

<regex_rule> ::= "- type: regex"
                 "value:" <regex_pattern>

<variable_equals_rule> ::= "- type: variable_equals"
                           "variable:" <identifier>  # 对应 session.variables 中的键名
                           "value:" <value>

<variable_exists_rule> ::= "- type: variable_exists"
                           "variable:" <variable>
```

### 2.6 基本类型

```bnf
<string> ::= '"' <any_character>* '"'

<regex_pattern> ::= <string>  # 符合Python re模块的正则表达式

<uri> ::= "database://" <path> | "https://" <path>

<variable> ::= "session." <identifier> | "session.variables." <identifier>

<value> ::= <string> | <number> | <boolean> | <template>

<template> ::= <string>  # 支持 {{variable}} 插值语法

<number> ::= <integer> | <float>

<boolean> ::= "true" | "false"
```

---

## 3. 语法元素详解

### 3.1 Flow（流程）

每个YAML文件定义一个流程，包含以下必需元素：

```yaml
name: "流程名称"           # 必需，流程的显示名称
entry_point: "state_id"    # 必需，流程的入口状态ID
description: "流程描述"     # 可选，流程功能说明
states:                    # 必需，状态列表
  - id: "state_1"
    # ... 状态定义
  - id: "state_2"
    # ... 状态定义
```

**示例**:
```yaml
name: "产品咨询流程"
entry_point: "state_start_inquiry"
description: "处理用户的产品查询和推荐请求"
states:
  # ... 状态定义
```

### 3.2 State（状态）

状态是流程的基本组成单元，每个状态可包含：

| 字段 | 必需 | 说明 |
|------|------|------|
| `id` | 是 | 状态唯一标识符 |
| `triggers` | 否 | 进入此状态的触发条件 |
| `actions` | 否 | 进入状态后执行的动作 |
| `transitions` | 否 | 离开状态的转换规则 |

**示例**:
```yaml
- id: "state_welcome"
  triggers:
    - type: regex
      value: ".*你好.*|.*hi.*"
  actions:
    - type: respond
      text: "您好！欢迎使用智能客服系统"
  transitions:
    - condition:
        all:
          - type: regex
            value: ".*产品.*|.*商品.*"
      target: "state_product_inquiry"
```

### 3.3 Trigger（触发器）

触发器定义何时进入某个状态（通常用于流程入口状态）。

**类型**:
- `regex`: 正则表达式匹配
- `keyword`: 关键词匹配（未完全实现）
- `intent`: LLM意图识别（未完全实现）

**示例**:
```yaml
triggers:
  - type: regex
    value: ".*退款.*|.*退货.*"
```

### 3.4 Action（动作）

动作定义进入状态后要执行的操作。

#### 3.4.1 respond - 回复用户

```yaml
- type: respond
  text: "这是回复内容，支持{{session.variable}}插值"
```

#### 3.4.2 api_call - 调用API

```yaml
- type: api_call
  endpoint: "database://products/list"
  params:
    category: "数码配件"
  save_to: "session.products"
```

#### 3.4.3 extract_variable - 提取变量

```yaml
- type: extract_variable
  regex: "[A-Z][0-9]{10}"  # 订单号格式
  save_to: "session.order_id"
```

#### 3.4.4 set_variable - 设置变量

```yaml
- type: set_variable
  scope: session
  key: "current_category"
  value: "数码配件"
```

#### 3.4.5 wait_for_input - 等待用户输入

```yaml
- type: wait_for_input
```

### 3.5 Transition（转换）

转换定义从当前状态到下一个状态的规则。

**结构**:
```yaml
transitions:
  - condition:    # 转换条件
      # ... 条件定义
    target: "state_next"  # 目标状态ID
```

**无条件转换**（兜底）:
```yaml
transitions:
  - target: "state_default"  # 没有condition字段
```

---

## 4. 数据类型

### 4.1 标量类型

| 类型 | YAML表示 | 示例 |
|------|----------|------|
| 字符串 | 带引号或不带引号 | `"你好"` 或 `你好` |
| 整数 | 数字 | `123` |
| 浮点数 | 带小数点的数字 | `299.99` |
| 布尔值 | true/false | `true` |

### 4.2 模板字符串

支持`{{variable}}`插值语法，运行时替换为实际值。

**示例**:
```yaml
text: "您的订单号是{{session.order_id}}，状态为{{session.order_status}}"
```

### 4.3 列表

```yaml
keywords:
  - "耳机"
  - "手环"
  - "充电宝"
```

### 4.4 字典

```yaml
params:
  category: "数码配件"
  min_price: 100
  max_price: 500
```

---

## 5. 内置动作类型

### 5.1 respond - 文本回复

**功能**: 向用户发送文本消息

**参数**:
- `text` (string, 必需): 回复文本，支持多行和模板插值

**示例**:
```yaml
- type: respond
  text: |
    欢迎来到智能客服！
    我可以帮您：
    1. 查询产品信息
    2. 查询订单状态
    3. 办理退款
```

**模板示例**:
```yaml
- type: respond
  text: "您选择的商品是{{session.product.name}}，价格{{session.product.price}}元"
```

### 5.2 api_call - API调用

**功能**: 调用数据库或外部API获取数据

**参数**:
- `endpoint` (string, 必需): API端点
- `params` (dict, 可选): 请求参数
- `save_to` (string, 可选): 保存结果的会话变量路径

**支持的端点**:

#### 数据库端点 (database://)

| 端点 | 说明 | 参数 |
|------|------|------|
| `database://products/list` | 查询产品列表 | `category` (可选) |
| `database://products/get` | 查询单个产品 | `product_id` (必需) |
| `database://products/search` | 搜索产品 | `keyword` (必需) |
| `database://orders/get` | 查询单个订单 | `order_id` (必需) |
| `database://orders/list` | 查询用户订单列表 | `user_id` (必需) |

**示例**:
```yaml
- type: api_call
  endpoint: "database://products/get"
  params:
    product_id: "P001"
  save_to: "session.current_product"
```

### 5.3 extract_variable - 变量提取

**功能**: 从用户输入中提取信息

**参数**:
- `regex` (string, 必需): 正则表达式
- `save_to` (string, 必需): 保存到的变量路径

**示例**:
```yaml
- type: extract_variable
  regex: "[A-Z][0-9]{10}"  # 匹配订单号格式
  save_to: "session.order_id"
```

### 5.4 set_variable - 变量设置

**功能**: 设置会话变量值

**参数**:
- `scope` (string, 必需): 作用域，目前固定为 `"session"`
- `key` (string, 必需): 会话变量名，对应 `session.variables[key]`
- `value` (any, 必需): 变量值

**示例**:
```yaml
- type: set_variable
  scope: session
  key: "refund_reason"
  value: "quality_issue"
```

### 5.5 wait_for_input - 等待输入

**功能**: 暂停流程，等待用户输入

**参数**: 无

**示例**:
```yaml
- type: wait_for_input
```

---

## 6. 条件匹配规则

### 6.1 条件类型

#### 6.1.1 all - 所有条件必须满足（AND逻辑）

```yaml
condition:
  all:
    - type: regex
      value: ".*确认.*"
    - type: variable_exists
      variable: "order_id"
```

#### 6.1.2 any - 任一条件满足即可（OR逻辑）

```yaml
condition:
  any:
    - type: regex
      value: ".*是的.*|.*对.*|.*确认.*"
    - type: regex
      value: ".*好的.*|.*OK.*"
```

### 6.2 规则类型

#### 6.2.1 regex - 正则表达式匹配

匹配用户输入是否符合正则表达式。

```yaml
- type: regex
  value: ".*退款.*|.*退货.*"
```

#### 6.2.2 variable_equals - 变量值比较

检查会话变量是否等于指定值。

```yaml
- type: variable_equals
  variable: "refund_reason"
  value: "quality_issue"
```

> 注意：这里的 `variable` 是存放在 `session.variables` 字典中的键名，例如 `refund_reason`、`order_id` 等。
> 在模板或 `save_to` 中则使用 `session.refund_reason`、`session.order_id` 这样的完整路径。

#### 6.2.3 variable_exists - 变量存在性检查

检查会话变量是否存在。

```yaml
- type: variable_exists
  variable: "order_id"
```

### 6.3 复杂条件示例

```yaml
condition:
  all:
    - type: variable_exists
      variable: "order_id"
    - type: any
        - type: regex
          value: ".*确认.*|.*是的.*"
        - type: regex
          value: ".*OK.*|.*好的.*"
```

---

## 7. 变量系统

### 7.1 变量作用域

所有变量存储在会话对象的`variables`字典中。

**访问方式**:
- `session.variables.order_id`
- `session.order_id` (简写)

### 7.2 内置变量

| 变量 | 说明 | 示例值 |
|------|------|--------|
| `session.session_id` | 会话ID | `"127.0.0.1:5001"` |
| `session.current_state_id` | 当前状态ID | `"state_collect_info"` |
| `session.last_user_input` | 最后用户输入 | `"我要买耳机"` |

### 7.3 自定义变量

通过`set_variable`或`save_to`创建。

**示例**:
```yaml
# 方式1: set_variable
- type: set_variable
  variable: "session.category"
  value: "数码配件"

# 方式2: api_call的save_to
- type: api_call
  endpoint: "database://products/get"
  params:
    product_id: "P001"
  save_to: "session.product"  # 保存整个产品对象
```

### 7.4 变量使用

在`text`和`params`中使用`{{variable}}`插值：

```yaml
- type: respond
  text: |
    商品名称：{{session.product.name}}
    价格：{{session.product.price}}元
    库存：{{session.product.stock}}件
```

---

## 8. 完整示例

### 8.1 简单示例：问候流程

```yaml
name: "通用闲聊"
entry_point: "state_start_chitchat"
description: "处理用户的日常问候"

states:
  - id: "state_start_chitchat"
    triggers:
      - type: regex
        value: ".*你好.*|.*hi.*|.*hello.*|.*嗨.*"
    actions:
      - type: respond
        text: "您好！我是智能客服，很高兴为您服务！有什么可以帮您的吗？"
    transitions:
      - target: "state_end_chitchat"

  - id: "state_end_chitchat"
    actions:
      - type: respond
        text: "祝您生活愉快！如有需要随时找我。"
```

### 8.2 中等复杂度：订单查询

```yaml
name: "订单查询流程"
entry_point: "state_start_order_query"

states:
  - id: "state_start_order_query"
    triggers:
      - type: regex
        value: ".*订单.*|.*查询.*"
    actions:
      - type: respond
        text: "请提供您的订单号（格式如：A1234567890）"
    transitions:
      - target: "state_collect_order_id"

  - id: "state_collect_order_id"
    actions:
      - type: extract_variable
        regex: "[A-Z][0-9]{10}"
        save_to: "session.order_id"
      - type: api_call
        endpoint: "database://orders/get"
        params:
          order_id: "{{session.order_id}}"
        save_to: "session.order"
      - type: respond
        text: |
          订单详情：
          订单号：{{session.order.order_id}}
          商品：{{session.order.product_name}}
          金额：{{session.order.total_price}}元
          状态：{{session.order.status}}
          物流单号：{{session.order.tracking_number}}
    transitions:
      - target: "state_end_query"

  - id: "state_end_query"
    actions:
      - type: respond
        text: "还有其他问题吗？"
```

### 8.3 复杂示例：产品咨询（简化版）

```yaml
name: "产品咨询流程"
entry_point: "state_start_inquiry"

states:
  - id: "state_start_inquiry"
    triggers:
      - type: regex
        value: ".*(产品|商品|购买|买).*"
    actions:
      - type: api_call
        endpoint: "database://products/list"
        save_to: "session.products"
      - type: respond
        text: |
          我们有以下产品：
          1. P001 - 蓝牙耳机（299元）
          2. P002 - 智能手环（199元）
          3. P003 - 移动充电宝（149元）

          请输入商品编号查看详情
    transitions:
      - condition:
          all:
            - type: regex
              value: "P[0-9]{3}"
        target: "state_show_product_detail"
      - target: "state_fallback"

  - id: "state_show_product_detail"
    actions:
      - type: extract_variable
        regex: "P[0-9]{3}"
        save_to: "session.product_id"
      - type: api_call
        endpoint: "database://products/get"
        params:
          product_id: "{{session.product_id}}"
        save_to: "session.product"
      - type: respond
        text: |
          商品详情：
          名称：{{session.product.name}}
          分类：{{session.product.category}}
          价格：{{session.product.price}}元
          库存：{{session.product.stock}}件
          描述：{{session.product.description}}

          是否购买？（回复"是"确认）
    transitions:
      - condition:
          any:
            - type: regex
              value: ".*是.*|.*确认.*|.*购买.*"
        target: "state_confirm_purchase"
      - target: "state_cancel"

  - id: "state_confirm_purchase"
    actions:
      - type: respond
        text: "好的，已为您记录购买意向。请联系客服完成下单。"
    transitions:
      - target: "state_end_inquiry"

  - id: "state_cancel"
    actions:
      - type: respond
        text: "好的，如需其他帮助请告诉我。"
    transitions:
      - target: "state_end_inquiry"

  - id: "state_fallback"
    actions:
      - type: respond
        text: "抱歉，我没理解您的意思，请重新输入商品编号。"
    transitions:
      - target: "state_start_inquiry"

  - id: "state_end_inquiry"
    actions:
      - type: respond
        text: "感谢您的咨询，祝您购物愉快！"
```

---

## 9. 最佳实践

### 9.1 命名规范

- **State ID**: 使用`state_`前缀，描述性命名
  - ✅ `state_collect_user_info`
  - ❌ `s1`, `temp_state`

- **Variable**: 使用小写+下划线
  - ✅ `session.order_id`
  - ❌ `session.OrderID`

### 9.2 状态设计

- **单一职责**: 每个状态只做一件事
- **明确出口**: 每个状态应有明确的转换规则
- **避免死循环**: 确保有退出条件

### 9.3 错误处理

- 使用兜底转换（无condition）处理未匹配情况
- 提供友好的错误提示
- 设计回退状态（fallback）

**示例**:
```yaml
transitions:
  - condition:
      all:
        - type: regex
          value: ".*正确输入.*"
    target: "state_next"
  - target: "state_error_fallback"  # 兜底
```

### 9.4 模板使用

- 使用多行字符串`|`提高可读性
- 模板变量使用完整路径避免歧义
- 提供默认值处理缺失变量

```yaml
text: |
  欢迎{{session.variables.user_name|default('用户')}}！
  您的订单{{session.order_id}}已发货。
```

### 9.5 流程模块化

- 按业务场景拆分流程文件
- 使用清晰的文件夹结构
- 添加充分的注释

```
dsl/flows/
  ├── pre_sales/         # 售前
  │   └── product_inquiry.yaml
  ├── in_sales/          # 售中
  │   └── order_management.yaml
  └── after_sales/       # 售后
      ├── refund.yaml
      └── invoice.yaml
```

---

## 10. 常见错误

### 10.1 语法错误

#### 错误1：缺少必需字段

```yaml
# ❌ 错误：缺少entry_point
name: "测试流程"
states:
  - id: "state_1"

# ✅ 正确
name: "测试流程"
entry_point: "state_1"
states:
  - id: "state_1"
```

#### 错误2：缩进错误

```yaml
# ❌ 错误：actions缩进不正确
- id: "state_1"
actions:
  - type: respond
    text: "你好"

# ✅ 正确
- id: "state_1"
  actions:
    - type: respond
      text: "你好"
```

### 10.2 逻辑错误

#### 错误3：无限循环

```yaml
# ❌ 错误：state_a和state_b互相跳转
- id: "state_a"
  transitions:
    - target: "state_b"

- id: "state_b"
  transitions:
    - target: "state_a"

# ✅ 正确：添加退出条件
- id: "state_a"
  transitions:
    - condition:
        all:
          - type: regex
            value: ".*退出.*"
      target: "state_end"
    - target: "state_b"
```

#### 错误4：变量未定义

```yaml
# ❌ 错误：使用未定义的变量
- type: respond
  text: "您的订单号是{{session.order_id}}"  # order_id未设置

# ✅ 正确：先提取/设置变量
- type: extract_variable
  regex: "[A-Z][0-9]{10}"
  save_to: "session.order_id"
- type: respond
  text: "您的订单号是{{session.order_id}}"
```

### 10.3 性能问题

#### 错误5：状态过多

```yaml
# ❌ 避免：一个流程100+个状态
states:
  - id: "state_1"
    # ...
  - id: "state_2"
    # ...
  # ... 100个状态

# ✅ 建议：拆分为多个子流程
```

---

## 附录A：正则表达式速查

| 模式 | 说明 | 示例匹配 |
|------|------|----------|
| `.*keyword.*` | 包含关键词 | "我想买耳机" 匹配 `.*耳机.*` |
| `^keyword` | 以关键词开头 | "退款申请" 匹配 `^退款` |
| `keyword$` | 以关键词结尾 | "申请退款" 匹配 `退款$` |
| `[A-Z][0-9]{10}` | 订单号格式 | "A1234567890" |
| `P[0-9]{3}` | 商品ID格式 | "P001", "P999" |
| `\\d+\\.?\\d*元` | 金额 | "299元", "199.5元" |
| `.*(是\|对\|确认).*` | 多选一 | "是的", "对", "确认" |

---

## 附录B：数据库端点完整列表

| 端点 | 方法 | 参数 | 返回值 |
|------|------|------|--------|
| `database://products/list` | GET | `category`(可选) | 产品列表 |
| `database://products/get` | GET | `product_id` | 单个产品 |
| `database://products/search` | GET | `keyword` | 搜索结果 |
| `database://orders/get` | GET | `order_id` | 单个订单 |
| `database://orders/list` | GET | `user_id` | 用户订单列表 |
| `database://refunds/check` | GET | `order_id` | 退款资格 |

---

**文档版本历史**:
- v1.0 (2025-11-16): 初始版本

**参考资料**:
- [YAML规范](https://yaml.org/)
- [Python正则表达式文档](https://docs.python.org/3/library/re.html)
- [有限状态机理论](https://en.wikipedia.org/wiki/Finite-state_machine)
