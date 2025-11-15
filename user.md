📖 用户使用说明
1. 系统安装
环境要求
Python 3.8+
Windows/Linux/Mac 操作系统
安装步骤
# 1. 克隆或下载项目
cd f:\Sandstorm\code\ChatFlowDSL

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. （可选）配置 OpenAI API 密钥
# Windows:
$env:OPENAI_API_KEY="sk-qerkanyrjlblvbuvztlmzufjaytkpzbaryvzprzngbjeuwag"


# Linux/Mac:
export OPENAI_API_KEY=your_api_key_here

# 4. 验证安装 - 运行集成测试
python -X utf8 tests/test_integration.py
预期输出：
============================================================
✓ 所有测试通过！
============================================================
测试1: 数据库功能                    ✓
测试2: LLM意图识别（降级模式）       ✓
测试3: 动作执行器（数据库集成）      ✓
测试4: 完整对话流程模拟              ✓
2. 快速启动
启动聊天机器人
# Windows 用户必须使用 -X utf8 参数
python -X utf8 main.py

# 或者设置环境变量
set PYTHONUTF8=1
python main.py
示例对话
场景 1：产品咨询
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
场景 2：订单查询
你: 查询订单
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
场景 3：查看所有订单
你: 查看我的订单
机器人: 您的订单列表如下：
• A1234567890 - 无线蓝牙耳机Pro [已发货]
• B9876543210 - 智能手环Max [已送达]
• C1122334455 - 便携充电宝20000mAh [待发货]

请告诉我订单号，我可以为您查询详细信息。
3. 系统配置
配置文件位置
config/config.yaml
主要配置项
# LLM 配置
llm:
  api_key: "YOUR_OPENAI_API_KEY"  # 可使用环境变量 OPENAI_API_KEY
  model_name: "gpt-3.5-turbo"     # 模型名称
  base_url: null                   # 自定义 API 端点（兼容其他 OpenAI 格式服务）

# 运行模式
mode: "hybrid"  # 可选: rule (纯规则), llm (纯LLM), hybrid (混合，推荐)

# 数据库配置
database:
  path: "data/chatbot.db"  # SQLite 数据库路径
  auto_init: true           # 自动初始化测试数据

# 会话配置
session:
  timeout: 3600      # 会话超时时间（秒）
  max_history: 50    # 最大历史记录条数

# 日志配置
logging:
  level: "INFO"               # DEBUG/INFO/WARNING/ERROR
  file: "logs/chatbot.log"    # 日志文件路径
  console: true               # 是否输出到控制台
使用其他 OpenAI 兼容服务
例如使用 Azure OpenAI、本地 LLM 服务等：
llm:
  api_key: "your_custom_api_key"
  model_name: "gpt-3.5-turbo"
  base_url: "https://your-custom-endpoint.com/v1"  # 自定义端点
4. 数据库说明
数据库文件
位置：data/chatbot.db
类型：SQLite 3
自动初始化：首次运行时自动创建并填充测试数据
预置测试数据
商品（5个）：
P001: 无线蓝牙耳机Pro - ¥299
P002: 智能手环Max - ¥199
P003: 便携充电宝20000mAh - ¥149
P004: 机械键盘RGB版 - ¥399
P005: 4K网络摄像头 - ¥599
用户（2个）：
U001: 张三 (手机: 13800138000)
U002: 李四 (手机: 13900139000)
订单（3个）：
A1234567890: 张三购买耳机，已发货
B9876543210: 张三购买手环，已送达
C1122334455: 李四购买充电宝，待发货
手动查询数据库
# 安装 SQLite 客户端（如果没有）
# Windows: 下载 sqlite3.exe
# Linux: sudo apt install sqlite3
# Mac: brew install sqlite3

# 连接数据库
sqlite3 data/chatbot.db

# 查询示例
SELECT * FROM products;
SELECT * FROM orders;
SELECT * FROM users;

# 退出
.quit
5. DSL 流程开发指南
流程文件位置
售前流程：dsl/flows/pre_sales/
售中流程：dsl/flows/in_sales/
售后流程：dsl/flows/after_sales/
通用流程：dsl/flows/general/
database:// 协议端点
在 DSL 中使用 database:// 协议直接查询数据库：
端点	功能	参数	返回值
database://products/list	获取商品列表	category (可选), limit (默认10)	商品列表
database://products/get	获取商品详情	product_id	单个商品对象
database://products/search	搜索商品	keyword	商品列表
database://orders/get	获取订单详情	order_id	订单对象（含商品名称）
database://orders/list	获取用户订单	user_id	订单列表
database://refunds/check	检查退款状态	order_id	退款记录
database://invoices/check_eligibility	检查发票资格	order_id	资格检查结果
DSL 示例：查询商品并显示
states:
  - id: "show_products"
    actions:
      # 1. 调用数据库查询
      - type: api_call
        endpoint: "database://products/list"
        params:
          limit: 5
        save_to: "session.featured_products"
      
      # 2. 显示结果（使用自动格式化变量）
      - type: respond
        text: |
          我们的商品有：
          {{session.products_list}}  # 自动格式化为编号列表
可用的自动格式化变量
系统会自动将复杂数据结构转换为易读文本：
变量名	说明	示例输出
{{session.products_list}}	商品列表	1. 耳机 - ¥299 (库存: 150)
{{session.order_status_text}}	订单状态中文	已发货 / 已送达
{{session.tracking_info}}	物流信息	物流单号：SF1234567890
{{session.current_product.features}}	产品特性列表	• 主动降噪\n• 30小时续航
{{session.order_list_text}}	订单列表	• A123... - 耳机 [已发货]
示例：完整订单查询流程
参考：dsl/flows/in_sales/order_management.yaml:55-79
- id: "state_query_specific_order"
  actions:
    # 提取订单号
    - type: extract_variable
      source: user_input
      regex: "(?P<order_id>[A-Z][0-9]{10})"
      target: "session.order_id"
    
    # 查询数据库
    - type: api_call
      endpoint: "database://orders/get"
      params: {}  # 自动从 session.order_id 读取
      save_to: "session.current_order"
    
    # 显示结果
    - type: respond
      text: |
        📦 订单详情
        
        订单号：{{session.current_order.order_id}}
        商品名称：{{session.current_order.product_name}}
        数量：{{session.current_order.quantity}} 件
        总价：¥{{session.current_order.total_price}}
        订单状态：{{session.order_status_text}}
        配送地址：{{session.current_order.shipping_address}}
        {{session.tracking_info}}
6. 测试指南
运行集成测试
# 完整集成测试（推荐）
python -X utf8 tests/test_integration.py

# 单独测试数据库
python -X utf8 core/database_manager.py

# 单独测试 LLM 响应器
python -X utf8 llm/llm_responder.py
测试覆盖范围
数据库功能测试：商品查询、订单查询、退款管理
LLM 意图识别测试：降级模式规则匹配
动作执行器测试：database:// 协议、模板渲染
完整对话流程测试：产品咨询→订单查询
预期测试结果
============================================================
ChatFlowDSL 集成测试套件
============================================================

测试1: 数据库功能                    ✓
测试2: LLM意图识别（降级模式）       ✓
测试3: 动作执行器（数据库集成）      ✓
测试4: 完整对话流程模拟              ✓

============================================================
✓ 所有测试通过！
============================================================
7. 故障排查
问题 1：编码错误（UnicodeEncodeError）
错误信息：
UnicodeEncodeError: 'gbk' codec can't encode character '\xa5'
解决方案：
# Windows 用户必须使用 UTF-8 模式
python -X utf8 main.py

# 或设置环境变量
set PYTHONUTF8=1
问题 2：数据库文件不存在
错误信息：
[DatabaseManager] 数据库不存在，正在初始化...
解决方案：这是正常行为，系统会自动创建数据库。如需重置数据库：
# 删除旧数据库
del data\chatbot.db  # Windows
rm data/chatbot.db   # Linux/Mac

# 重新运行程序，自动重建
python -X utf8 main.py
问题 3：LLM API 调用失败
错误信息：
[LLM API调用失败] ...
[使用降级规则匹配] 输入: '...'
解决方案：这是正常的降级行为。如需启用真实 LLM：
# 1. 设置有效的 API 密钥
set OPENAI_API_KEY=sk-your-real-api-key

# 2. 或在 config/config.yaml 中配置
llm:
  api_key: "sk-your-real-api-key"
  model_name: "gpt-3.5-turbo"
问题 4：依赖包缺失
错误信息：
ModuleNotFoundError: No module named 'openai'
解决方案：
pip install -r requirements.txt
8. 进阶使用
添加新商品到数据库
from core.database_manager import DatabaseManager

db = DatabaseManager()
db.add_product({
    "product_id": "P006",
    "name": "无线鼠标",
    "category": "数码",
    "price": 89.0,
    "stock": 200,
    "description": "人体工学设计，2.4G无线连接",
    "features": ["人体工学", "无线连接", "静音按键"]
})
创建新的 DSL 流程
在 dsl/flows/ 下创建新的 YAML 文件
定义状态和转换逻辑
在 core/chatbot.py 中注册流程
自定义意图识别规则
编辑 llm/llm_responder.py:146-177 中的 rules 列表：
rules = [
    {
        "patterns": ["自定义关键词1", "自定义关键词2"],
        "intent": "自定义意图名称",
        "confidence": 0.85
    },
    # ... 更多规则
]
9. 参考文档
项目总览：README.md
更新日志：CHANGELOG.md
LLM 使用指南：docs/llm_usage.md
集成测试示例：tests/test_integration.py
10. 常见问题 FAQ
Q: 系统是否必须配置 OpenAI API 才能运行？ A: 不是。系统有降级机制，未配置 API 时会自动使用规则匹配，功能完全正常。 Q: 如何添加新的数据库查询端点？ A: 在 core/action_executor.py:98-163 的 _handle_database_query() 方法中添加新的 elif 分支。 Q: 支持哪些 OpenAI 兼容服务？ A: 任何兼容 OpenAI Chat Completion API 的服务，包括 Azure OpenAI, Claude via API, 本地 LLM 等。 Q: 如何修改默认用户？ A: 在订单查询流程中，默认使用 user_id: "U001"。可在 DSL 文件中修改或从 session 中动态获取。
🎯 总结
当前系统已实现：
✅ 完整的 LLM API 集成（支持降级）
✅ SQLite 数据库支持（6个表，完整CRUD）
✅ 真实的网购场景流程
✅ database:// 协议集成
✅ 智能模板渲染
✅ 集成测试覆盖
系统已可投入实际使用，用户可以：
直接运行体验完整对话流程
基于 DSL 开发新的业务流程
扩展数据库表结构
自定义意图识别规则
下一步建议：
完成课程要求的文档（需求分析、设计说明、测试报告）
录制演示视频
准备答辩 PPT
启用真实 LLM API 进行效果对比
如有任何问题，请参考上述文档或查看源代码注释！