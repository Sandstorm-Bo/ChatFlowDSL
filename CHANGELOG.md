# 🎉 ChatFlowDSL 新功能更新

## 更新概要

已成功实现 **LLM API 集成** 和 **数据库支持**，现在系统具备完整的网购场景业务逻辑！

---

## ✨ 新增功能

### 1. LLM API 集成 (OpenAI 兼容接口)

#### 功能特性
- ✅ **意图识别**：自动识别用户输入的意图类型
- ✅ **实体提取**：从用户输入中提取关键信息（订单号、产品名称等）
- ✅ **智能回复**：基于上下文生成自然语言响应
- ✅ **降级机制**：API调用失败时自动降级到规则匹配

#### 使用方式

**文件位置**: [llm/llm_responder.py](llm/llm_responder.py)

```python
from llm.llm_responder import LLMResponder

# 初始化（支持OpenAI兼容接口）
responder = LLMResponder(
    api_key="your_api_key",
    model_name="gpt-3.5-turbo",
    base_url=[None](https://api.siliconflow.cn/v1)  # 可选：自定义API端点
)

# 意图识别
result = responder.recognize_intent("我想退款")
# 返回: {"intent": "退款退货", "confidence": 0.9, "entities": {...}}

# 实体提取
entities = responder.extract_entities("订单A1234567890退款299元", ["订单号", "金额"])
# 返回: {"订单号": "A1234567890", "金额": "299元"}
```

#### 配置说明

在 [config/config.yaml](config/config.yaml) 中配置：

```yaml
llm:
  api_key: "YOUR_OPENAI_API_KEY"  # 或使用环境变量 OPENAI_API_KEY
  model_name: "gpt-3.5-turbo"
  base_url: null  # 自定义端点，如其他OpenAI兼容服务

mode: "hybrid"  # rule/llm/hybrid
```

---

### 2. SQLite 数据库支持

#### 数据库表结构

**文件位置**: [core/database_manager.py](core/database_manager.py)

| 表名 | 说明 | 主要字段 |
|------|------|----------|
| `users` | 用户信息 | user_id, username, phone, email, address |
| `products` | 商品信息 | product_id, name, category, price, stock, description, features |
| `orders` | 订单信息 | order_id, user_id, product_id, quantity, total_price, status, tracking_number |
| `refunds` | 退款记录 | refund_id, order_id, reason, reason_type, amount, status |
| `invoices` | 发票记录 | invoice_id, order_id, invoice_title, tax_id, amount, status |
| `service_records` | 客服记录 | record_id, user_id, session_id, issue_type, status |

#### 预置测试数据

系统已预置完整的测试数据：
- **5个商品**：无线蓝牙耳机Pro、智能手环Max、充电宝、机械键盘、摄像头
- **2个用户**：张三(U001)、李四(U002)
- **3个订单**：涵盖已发货、已送达、待发货等不同状态

#### 使用方式

```python
from core.database_manager import DatabaseManager

db = DatabaseManager()

# 商品查询
products = db.get_all_products(limit=5)
product = db.get_product("P001")

# 商品搜索
results = db.search_products("耳机")

# 订单管理
order = db.get_order("A1234567890")
user_orders = db.get_user_orders("U001")
db.update_order_status("A1234567890", "shipped", "SF1234567890")

# 退款管理
db.create_refund({
    "refund_id": "R001",
    "order_id": "A1234567890",
    "user_id": "U001",
    "amount": 299.0,
    "reason_type": "quality_issue"
})
```

---

### 3. 增强的 ActionExecutor

#### database:// 协议

**文件位置**: [core/action_executor.py](core/action_executor.py)

在 DSL 流程中可以直接使用 `database://` 协议查询数据库：

```yaml
actions:
  - type: api_call
    endpoint: "database://products/list"
    params:
      limit: 5
    save_to: "session.featured_products"
```

#### 支持的端点

| 端点 | 说明 | 参数 |
|------|------|------|
| `database://products/list` | 获取商品列表 | category, limit |
| `database://products/get` | 获取商品详情 | product_id |
| `database://products/search` | 搜索商品 | keyword |
| `database://orders/get` | 获取订单详情 | order_id |
| `database://orders/list` | 获取用户订单列表 | user_id |
| `database://refunds/check` | 检查退款状态 | order_id |
| `database://invoices/check_eligibility` | 检查发票资格 | order_id |

#### 模板渲染增强

ActionExecutor 现在支持复杂数据结构的自动格式化：

```yaml
actions:
  - type: respond
    text: |
      商品列表：
      {{session.products_list}}  # 自动格式化为列表

      订单状态：{{session.order_status_text}}  # 自动翻译状态
```

**自动处理的特殊变量**：
- `session.products_list` - 产品列表格式化
- `session.order_status_text` - 订单状态中文化
- `session.tracking_info` - 物流信息格式化
- `session.current_product.features` - 产品特性列表化

---

### 4. 更新的 DSL 流程

#### 产品咨询流程增强

**文件位置**: [dsl/flows/pre_sales/product_inquiry.yaml](dsl/flows/pre_sales/product_inquiry.yaml)

- ✅ 从数据库动态加载5个真实商品
- ✅ 支持按产品ID查询详细信息
- ✅ 展示价格、库存、产品特性
- ✅ 支持产品搜索功能

#### 订单管理流程增强

**文件位置**: [dsl/flows/in_sales/order_management.yaml](dsl/flows/in_sales/order_management.yaml)

- ✅ 查询用户所有订单
- ✅ 查询特定订单详情（状态、物流）
- ✅ 订单取消功能
- ✅ 状态智能翻译（已发货、已送达等）

---

## 🧪 测试

### 运行集成测试

```bash
# Windows
python -X utf8 tests/test_integration.py

# Linux/Mac
python tests/test_integration.py
```

### 测试数据库功能

```bash
python -X utf8 core/database_manager.py
```

### 测试 LLM 响应器

```bash
python -X utf8 llm/llm_responder.py
```

---

## 📊 测试结果

```
============================================================
✓ 所有测试通过！
============================================================

测试1: 数据库功能                    ✓
测试2: LLM意图识别（降级模式）       ✓
测试3: 动作执行器（数据库集成）      ✓
测试4: 完整对话流程模拟              ✓
```

---

## 🚀 运行完整系统

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API 密钥（可选，不配置会使用降级规则匹配）
set OPENAI_API_KEY=your_api_key  # Windows
export OPENAI_API_KEY=your_api_key  # Linux/Mac

# 3. 运行系统
python -X utf8 main.py
```

### 测试对话示例

```
正在初始化机器人...
[Chatbot] 加载流程: 售前产品咨询流程
[Chatbot] 加载流程: 售中订单管理流程
[Chatbot] 加载流程: 标准退款流程
[Chatbot] 加载流程: 发票申请流程
[Chatbot] 加载流程: 耳机故障排查流程
[Chatbot] 加载流程: 简单问候流程
Chatbot已启动，可以开始聊天 (输入 'quit', 'exit' 或 '退出' 结束)

你: 你好
机器人: 您好！很高兴为您服务，请问有什么可以帮您的？

你: 我想看看产品
机器人: 您好！欢迎了解我们的产品。我们有以下商品：
1. 无线蓝牙耳机Pro - ¥299.0 (库存: 150)
2. 智能手环Max - ¥199.0 (库存: 200)
3. 便携充电宝20000mAh - ¥149.0 (库存: 300)
4. 机械键盘RGB版 - ¥399.0 (库存: 80)
5. 4K网络摄像头 - ¥599.0 (库存: 50)

请告诉我您对哪款产品感兴趣，或者直接说出产品名称。

你: 耳机
机器人: 【无线蓝牙耳机Pro】
💰 价格：¥299.0
📦 库存：150 件

产品特点：
• 主动降噪
• 30小时续航
• 快速充电
• IPX4防水

产品描述：
高品质无线蓝牙耳机，支持主动降噪

您想了解更多详情还是直接购买呢？

你: 查一下我的订单
机器人: 您好！我可以帮您：
1. 查询订单状态和物流信息
2. 查看您的所有订单

请告诉我您的订单号（如：A1234567890），或者说"查看我的订单"。

你: A1234567890
机器人: 📦 订单详情

订单号：A1234567890
商品名称：无线蓝牙耳机Pro
数量：1 件
总价：¥299.0
订单状态：已发货
配送地址：北京市朝阳区xx街道xx号
物流单号：SF1234567890

您需要其他帮助吗？
```

---

## 📂 新增文件

- [core/database_manager.py](core/database_manager.py) - 数据库管理器
- [llm/llm_responder.py](llm/llm_responder.py) - LLM响应器（完全重写）
- [tests/test_integration.py](tests/test_integration.py) - 集成测试脚本
- `data/chatbot.db` - SQLite数据库文件（自动生成）

## 📝 修改文件

- [core/action_executor.py](core/action_executor.py) - 增加数据库查询、模板渲染增强
- [config/config.yaml](config/config.yaml) - 新增数据库、LLM配置
- [dsl/flows/pre_sales/product_inquiry.yaml](dsl/flows/pre_sales/product_inquiry.yaml) - 使用真实数据库
- [dsl/flows/in_sales/order_management.yaml](dsl/flows/in_sales/order_management.yaml) - 完整订单管理流程

---

## 🎯 核心优势

### 1. 真实业务场景
- ✅ 完整的网购场景：商品浏览→下单→订单查询→售后
- ✅ 真实的数据库支持，不是Mock数据
- ✅ 多表关联（用户-订单-商品-退款-发票）

### 2. LLM 智能增强
- ✅ 意图识别更准确
- ✅ 支持自然语言理解
- ✅ 降级机制保证系统可用性

### 3. 易于扩展
- ✅ `database://` 协议易于添加新端点
- ✅ 模板系统自动处理复杂数据结构
- ✅ DSL流程与数据库解耦

---

## 💡 下一步建议

1. **启用真实 LLM API**
   - 设置有效的 OpenAI API 密钥
   - 测试意图识别准确度
   - 调整 prompt 优化识别效果

2. **扩展数据库功能**
   - 添加购物车表
   - 实现真实下单流程
   - 添加支付状态跟踪

3. **完善业务流程**
   - 实现流程间跳转（产品咨询→下单→订单查询）
   - 添加更多产品类别
   - 实现用户登录/注册

4. **编写自动化测试**
   - 单元测试
   - 端到端测试
   - 性能测试

---

## 📞 支持

如有问题，请查看：
- [README.md](README.md) - 项目总体说明
- [docs/llm_usage.md](docs/llm_usage.md) - LLM使用指南
- [tests/test_integration.py](tests/test_integration.py) - 集成测试示例

---

**更新时间**: 2025-01-15
**版本**: v2.0 - 数据库与LLM集成版
