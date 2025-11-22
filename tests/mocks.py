"""
测试桩（Test Stubs/Mocks）

用途：
1. Mock LLM API - 避免真实API调用，提高测试速度
2. Mock数据库 - 内存数据库，快速测试
3. 提供可预测的测试数据

课设说明：
测试桩是软件测试的重要组成部分，用于隔离被测模块的外部依赖。
本文件提供了LLM API和数据库的Mock实现，使得测试可以：
- 快速执行（无网络延迟）
- 结果可预测（无随机性）
- 离线运行（无需API密钥）
"""

import re
from typing import Dict, Any, List, Optional
import sqlite3


class MockLLMResponder:
    """
    Mock LLM响应器

    使用简单的规则匹配代替真实的LLM API调用
    适用于单元测试和集成测试

    对齐真实 LLMResponder 的部分接口：
    - recognize_intent
    - check_semantic_match
    - match_condition_with_llm
    - generate_response
    """

    def __init__(self):
        """初始化Mock LLM"""
        # 定义意图识别规则（关键词匹配）
        self.intent_rules = {
            "产品咨询": ["耳机", "手环", "充电宝", "键盘", "摄像头", "商品", "产品", "买", "购买", "推荐"],
            "订单查询": ["订单", "查询订单", "我的订单", "订单号"],
            "退款退货": ["退款", "退货", "不想要", "质量问题", "七天无理由"],
            "发票申请": ["发票", "开票", "开发票", "增值税"],
            "故障报修": ["坏了", "不能用", "故障", "维修", "问题", "蓝牙", "连不上"],
            "闲聊问候": ["你好", "hi", "hello", "嗨", "在吗"],
        }

        # 定义实体提取规则
        self.entity_patterns = {
            "订单号": r"[A-Z][0-9]{10}",  # 如 A1234567890
            "金额": r"(\d+\.?\d*)\s*元",
            "商品ID": r"P\d{3}",  # 如 P001
            "手机号": r"1[3-9]\d{9}",
            "税号": r"\d{15,20}",
        }

    # -------- 基础 Mock 能力 --------

    def recognize_intent(self, text: str, context: Optional[Dict] = None) -> str:
        """
        识别用户意图（简单关键词匹配版本）

        Args:
            text: 用户输入
            context: 上下文信息（未使用，保持接口兼容）

        Returns:
            意图名称
        """
        text_lower = text.lower()

        # 按关键词匹配意图
        for intent, keywords in self.intent_rules.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return intent

        # 默认意图
        return "闲聊问候"

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        提取实体（Mock版本）

        Args:
            text: 用户输入

        Returns:
            实体字典，格式：{实体类型: [实体值列表]}
        """
        entities = {}

        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                entities[entity_type] = matches

        return entities

    def generate_response(self, prompt: str, context: Optional[Dict] = None) -> str:
        """
        生成回复（Mock版本）

        Args:
            prompt: 提示词
            context: 上下文信息

        Returns:
            Mock回复
        """
        if "产品" in prompt or "商品" in prompt:
            return "我们有多款优质商品，包括耳机、手环、充电宝等，请问您对哪类商品感兴趣？"
        if "订单" in prompt:
            return "请提供您的订单号，我帮您查询订单详情。"
        if "退款" in prompt:
            return "我理解您想要退款，请告诉我订单号和退款原因。"
        return "您好！有什么可以帮您的吗？"

    # -------- 对齐 LLMResponder 的高级接口 --------

    def check_semantic_match(
        self,
        user_input: str,
        semantic_meaning: str,
        session_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        语义匹配 Mock：用简单关键词近似实现

        返回结构与真实 LLMResponder 保持一致：
        {
            "matched": bool,
            "confidence": 0.0-1.0,
            "reasoning": "字符串"
        }
        """
        text = user_input.lower()
        meaning = semantic_meaning.lower()

        # 非严格：只要语义描述中的关键词出现在输入里，就认为匹配
        # 例如 semantic_meaning = "商品质量不满意"
        keywords = re.findall(r"[\u4e00-\u9fa5a-zA-Z0-9]+", meaning)
        hit = any(k and k in text for k in keywords)

        return {
            "matched": hit,
            "confidence": 0.9 if hit else 0.1,
            "reasoning": f"Mock 匹配：{'命中' if hit else '未命中'} 关键词 {keywords}",
        }

    def match_condition_with_llm(
        self,
        user_input: str,
        condition_description: str,
        available_targets: List[str],
        session_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        多路条件匹配 Mock：
        简单地在 user_input 中搜索 target 文本，命中的优先，未命中则返回第一个。

        返回结构：
        {
            "target": "目标名称",
            "confidence": 0.0-1.0,
            "reasoning": "字符串"
        }
        """
        text = user_input.lower()

        for target in available_targets:
            if target and str(target).lower() in text:
                return {
                    "target": target,
                    "confidence": 0.9,
                    "reasoning": f"Mock 匹配：在输入中找到了 '{target}'",
                }

        # 默认兜底：选择第一个目标
        fallback = available_targets[0] if available_targets else ""
        return {
            "target": fallback,
            "confidence": 0.5,
            "reasoning": "Mock 匹配：未命中任何目标，返回第一个作为兜底",
        }


class MockDatabaseManager:
    """
    Mock数据库管理器

    使用内存SQLite数据库，提供与真实数据库相同的主要接口
    适用于快速测试，无需持久化
    """

    def __init__(self, use_memory: bool = True):
        """
        初始化Mock数据库

        Args:
            use_memory: 是否使用内存数据库（默认True）
        """
        self.db_path = ":memory:" if use_memory else "test_chatbot.db"
        self.conn: Optional[sqlite3.Connection] = None
        self._init_database()
        self._init_test_data()

    def _get_connection(self):
        """获取数据库连接"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        return self.conn

    def _init_database(self):
        """初始化数据库表结构"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 商品表（精简版）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT,
                price REAL,
                stock INTEGER,
                description TEXT
            )
        """)

        # 订单表（精简版）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                user_id TEXT,
                product_id TEXT,
                product_name TEXT,
                quantity INTEGER,
                total_price REAL,
                status TEXT,
                tracking_number TEXT
            )
        """)

        conn.commit()

    def _init_test_data(self):
        """初始化测试数据"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 插入测试商品
        test_products = [
            ("P001", "蓝牙耳机", "数码配件", 299.00, 100, "高品质蓝牙耳机"),
            ("P002", "智能手环", "智能穿戴", 199.00, 50, "运动健康监测手环"),
            ("P003", "移动充电宝", "数码配件", 149.00, 200, "20000mAh大容量"),
        ]

        cursor.executemany(
            "INSERT OR IGNORE INTO products VALUES (?, ?, ?, ?, ?, ?)",
            test_products
        )

        # 插入测试订单
        test_orders = [
            ("A1234567890", "U001", "P001", "蓝牙耳机", 1, 299.00, "shipped", "SF1234567890"),
            ("B1234567890", "U001", "P002", "智能手环", 2, 398.00, "delivered", "SF0987654321"),
        ]

        cursor.executemany(
            "INSERT OR IGNORE INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            test_orders
        )

        conn.commit()

    def get_product(self, product_id: str) -> Optional[Dict]:
        """查询单个商品"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE product_id = ?", (product_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_products(self, category: Optional[str] = None) -> List[Dict]:
        """查询商品列表"""
        conn = self._get_connection()
        cursor = conn.cursor()

        if category:
            cursor.execute("SELECT * FROM products WHERE category = ?", (category,))
        else:
            cursor.execute("SELECT * FROM products")

        return [dict(row) for row in cursor.fetchall()]

    def get_order(self, order_id: str) -> Optional[Dict]:
        """查询单个订单"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_user_orders(self, user_id: str) -> List[Dict]:
        """查询用户所有订单"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE user_id = ?", (user_id,))
        return [dict(row) for row in cursor.fetchall()]

    # -------- 额外接口：对齐真实 DatabaseManager 的常用方法 --------

    def search_products(self, keyword: str) -> List[Dict[str, Any]]:
        """
        根据关键词搜索商品（名称/描述模糊匹配）
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        like = f"%{keyword}%"
        cursor.execute(
            "SELECT * FROM products WHERE name LIKE ? OR description LIKE ?",
            (like, like),
        )
        return [dict(row) for row in cursor.fetchall()]

    def add_order(self, order_data: Dict[str, Any]) -> bool:
        """
        创建订单（简化版）
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO orders (order_id, user_id, product_id, product_name,
                                    quantity, total_price, status, tracking_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order_data.get("order_id"),
                    order_data.get("user_id"),
                    order_data.get("product_id"),
                    order_data.get("product_name"),
                    order_data.get("quantity", 1),
                    order_data.get("total_price", 0.0),
                    order_data.get("status", "pending"),
                    order_data.get("tracking_number", ""),
                ),
            )
            conn.commit()
            return True
        except Exception:
            return False

    def update_order_status(self, order_id: str, status: str) -> bool:
        """
        更新订单状态
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE orders SET status = ? WHERE order_id = ?",
            (status, order_id),
        )
        conn.commit()
        return cursor.rowcount > 0

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None


# 便捷函数：创建Mock实例
def create_mock_llm() -> MockLLMResponder:
    """创建Mock LLM实例"""
    return MockLLMResponder()


def create_mock_db() -> MockDatabaseManager:
    """创建Mock数据库实例"""
    return MockDatabaseManager(use_memory=True)


# 示例用法
if __name__ == "__main__":
    print("=" * 60)
    print("测试桩演示")
    print("=" * 60)

    # 测试Mock LLM
    print("\n1. Mock LLM 意图识别测试")
    print("-" * 60)
    mock_llm = create_mock_llm()

    test_texts = [
        "我想买耳机",
        "查询订单A1234567890",
        "我要退款",
        "你好",
    ]

    for text in test_texts:
        intent = mock_llm.recognize_intent(text)
        entities = mock_llm.extract_entities(text)
        print(f"输入: {text}")
        print(f"  意图: {intent}")
        print(f"  实体: {entities}")

    # 测试Mock数据库
    print("\n2. Mock数据库测试")
    print("-" * 60)
    mock_db = create_mock_db()

    # 查询商品
    product = mock_db.get_product("P001")
    print(f"商品P001: {product}")

    # 查询订单
    order = mock_db.get_order("A1234567890")
    print(f"订单A1234567890: {order}")

    # 查询用户订单列表
    orders = mock_db.list_user_orders("U001")
    print(f"用户U001的订单数: {len(orders)}")

    mock_db.close()

    print("\n" + "=" * 60)
    print("测试桩可用于单元测试，避免真实API调用")
    print("=" * 60)
