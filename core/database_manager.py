import sqlite3
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import os


class DatabaseManager:
    """
    数据库管理器
    管理SQLite数据库，提供商品、订单、用户等数据的增删改查功能
    """

    def __init__(self, db_path: str = "data/chatbot.db"):
        """
        初始化数据库管理器

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()

    def _ensure_db_directory(self):
        """确保数据库目录存在"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使用Row工厂，可以通过列名访问
        return conn

    def _init_database(self):
        """初始化数据库表结构"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                address TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 商品表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT,
                price REAL NOT NULL,
                stock INTEGER DEFAULT 0,
                description TEXT,
                features TEXT,  -- JSON格式存储特性列表
                image_url TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 订单表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                total_price REAL NOT NULL,
                status TEXT DEFAULT 'pending',  -- pending, paid, shipped, delivered, cancelled
                shipping_address TEXT,
                tracking_number TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
        """)

        # 退款表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS refunds (
                refund_id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                reason TEXT,
                reason_type TEXT,  -- quality_issue, no_reason, wrong_item, etc.
                amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',  -- pending, approved, rejected, completed
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                processed_at TEXT,
                FOREIGN KEY (order_id) REFERENCES orders(order_id)
            )
        """)

        # 发票表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                invoice_id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                invoice_title TEXT NOT NULL,
                tax_id TEXT,
                invoice_type TEXT,  -- personal, company
                amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',  -- pending, issued, sent
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                issued_at TEXT,
                FOREIGN KEY (order_id) REFERENCES orders(order_id)
            )
        """)

        # 客服记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS service_records (
                record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                session_id TEXT,
                issue_type TEXT,
                issue_description TEXT,
                status TEXT DEFAULT 'open',  -- open, in_progress, resolved, closed
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                resolved_at TEXT
            )
        """)

        conn.commit()
        conn.close()

        # 初始化测试数据
        self._init_test_data()

    def _init_test_data(self):
        """初始化测试数据"""
        # 检查是否已有数据
        if self.get_product_count() > 0:
            return

        # 添加测试用户
        self.add_user({
            "user_id": "U001",
            "username": "张三",
            "phone": "13800138000",
            "email": "zhangsan@example.com",
            "address": "北京市朝阳区xx街道xx号"
        })

        self.add_user({
            "user_id": "U002",
            "username": "李四",
            "phone": "13900139000",
            "email": "lisi@example.com",
            "address": "上海市浦东新区xx路xx号"
        })

        # 添加测试商品
        products = [
            {
                "product_id": "P001",
                "name": "无线蓝牙耳机Pro",
                "category": "数码配件",
                "price": 299.00,
                "stock": 150,
                "description": "高品质无线蓝牙耳机，支持主动降噪",
                "features": json.dumps(["主动降噪", "30小时续航", "快速充电", "IPX4防水"], ensure_ascii=False),
                "image_url": "https://example.com/images/headset_pro.jpg"
            },
            {
                "product_id": "P002",
                "name": "智能手环Max",
                "category": "智能穿戴",
                "price": 199.00,
                "stock": 200,
                "description": "多功能智能手环，健康监测专家",
                "features": json.dumps(["心率监测", "睡眠分析", "运动追踪", "50米防水"], ensure_ascii=False),
                "image_url": "https://example.com/images/band_max.jpg"
            },
            {
                "product_id": "P003",
                "name": "便携充电宝20000mAh",
                "category": "数码配件",
                "price": 149.00,
                "stock": 300,
                "description": "大容量快充移动电源",
                "features": json.dumps(["20000mAh大容量", "双向快充", "多设备同充", "LED电量显示"], ensure_ascii=False),
                "image_url": "https://example.com/images/powerbank.jpg"
            },
            {
                "product_id": "P004",
                "name": "机械键盘RGB版",
                "category": "电脑外设",
                "price": 399.00,
                "stock": 80,
                "description": "专业机械键盘，游戏办公两相宜",
                "features": json.dumps(["青轴手感", "RGB背光", "全键无冲", "铝合金面板"], ensure_ascii=False),
                "image_url": "https://example.com/images/keyboard.jpg"
            },
            {
                "product_id": "P005",
                "name": "4K网络摄像头",
                "category": "电脑外设",
                "price": 599.00,
                "stock": 50,
                "description": "高清视频会议摄像头",
                "features": json.dumps(["4K超清", "自动对焦", "降噪麦克风", "广角镜头"], ensure_ascii=False),
                "image_url": "https://example.com/images/webcam.jpg"
            }
        ]

        for product in products:
            self.add_product(product)

        # 添加测试订单
        orders = [
            {
                "order_id": "A1234567890",
                "user_id": "U001",
                "product_id": "P001",
                "product_name": "无线蓝牙耳机Pro",
                "quantity": 1,
                "total_price": 299.00,
                "status": "shipped",
                "shipping_address": "北京市朝阳区xx街道xx号",
                "tracking_number": "SF1234567890"
            },
            {
                "order_id": "B9876543210",
                "user_id": "U002",
                "product_id": "P002",
                "product_name": "智能手环Max",
                "quantity": 2,
                "total_price": 398.00,
                "status": "delivered",
                "shipping_address": "上海市浦东新区xx路xx号",
                "tracking_number": "YT9876543210"
            },
            {
                "order_id": "C1122334455",
                "user_id": "U001",
                "product_id": "P003",
                "product_name": "便携充电宝20000mAh",
                "quantity": 1,
                "total_price": 149.00,
                "status": "paid",
                "shipping_address": "北京市朝阳区xx街道xx号",
                "tracking_number": ""
            }
        ]

        for order in orders:
            self.add_order(order)

    # ==================== 用户相关操作 ====================

    def add_user(self, user_data: Dict[str, Any]) -> bool:
        """添加用户"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (user_id, username, phone, email, address)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_data["user_id"],
                user_data["username"],
                user_data.get("phone"),
                user_data.get("email"),
                user_data.get("address")
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[添加用户失败] {str(e)}")
            return False

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    # ==================== 商品相关操作 ====================

    def add_product(self, product_data: Dict[str, Any]) -> bool:
        """添加商品"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO products (product_id, name, category, price, stock, description, features, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                product_data["product_id"],
                product_data["name"],
                product_data.get("category"),
                product_data["price"],
                product_data.get("stock", 0),
                product_data.get("description"),
                product_data.get("features"),
                product_data.get("image_url")
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[添加商品失败] {str(e)}")
            return False

    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """获取商品详情"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE product_id = ?", (product_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            product = dict(row)
            # 解析JSON字段
            if product.get("features"):
                try:
                    product["features"] = json.loads(product["features"])
                except:
                    pass
            return product
        return None

    def get_all_products(self, category: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """获取商品列表"""
        conn = self._get_connection()
        cursor = conn.cursor()

        if category:
            cursor.execute(
                "SELECT * FROM products WHERE category = ? AND stock > 0 LIMIT ?",
                (category, limit)
            )
        else:
            cursor.execute("SELECT * FROM products WHERE stock > 0 LIMIT ?", (limit,))

        rows = cursor.fetchall()
        conn.close()

        products = []
        for row in rows:
            product = dict(row)
            # 解析JSON字段
            if product.get("features"):
                try:
                    product["features"] = json.loads(product["features"])
                except:
                    pass
            products.append(product)

        return products

    def get_product_count(self) -> int:
        """获取商品总数"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def search_products(self, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
        """搜索商品"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM products
            WHERE (name LIKE ? OR description LIKE ? OR category LIKE ?)
            AND stock > 0
            LIMIT ?
        """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit))
        rows = cursor.fetchall()
        conn.close()

        products = []
        for row in rows:
            product = dict(row)
            if product.get("features"):
                try:
                    product["features"] = json.loads(product["features"])
                except:
                    pass
            products.append(product)

        return products

    # ==================== 订单相关操作 ====================

    def add_order(self, order_data: Dict[str, Any]) -> bool:
        """创建订单"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO orders (order_id, user_id, product_id, product_name, quantity, total_price, status, shipping_address, tracking_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                order_data["order_id"],
                order_data["user_id"],
                order_data["product_id"],
                order_data["product_name"],
                order_data["quantity"],
                order_data["total_price"],
                order_data.get("status", "pending"),
                order_data.get("shipping_address"),
                order_data.get("tracking_number", "")
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[创建订单失败] {str(e)}")
            return False

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """获取订单详情"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def get_user_orders(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取用户的订单列表"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM orders
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, limit))
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def update_order_status(self, order_id: str, status: str, tracking_number: Optional[str] = None) -> bool:
        """更新订单状态"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if tracking_number:
                cursor.execute("""
                    UPDATE orders
                    SET status = ?, tracking_number = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE order_id = ?
                """, (status, tracking_number, order_id))
            else:
                cursor.execute("""
                    UPDATE orders
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE order_id = ?
                """, (status, order_id))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[更新订单状态失败] {str(e)}")
            return False

    # ==================== 退款相关操作 ====================

    def create_refund(self, refund_data: Dict[str, Any]) -> bool:
        """创建退款申请"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO refunds (refund_id, order_id, user_id, reason, reason_type, amount, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                refund_data["refund_id"],
                refund_data["order_id"],
                refund_data["user_id"],
                refund_data.get("reason"),
                refund_data.get("reason_type"),
                refund_data["amount"],
                refund_data.get("status", "pending")
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[创建退款失败] {str(e)}")
            return False

    def get_refund_by_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """根据订单号查询退款"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM refunds WHERE order_id = ? ORDER BY created_at DESC LIMIT 1", (order_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    # ==================== 发票相关操作 ====================

    def create_invoice(self, invoice_data: Dict[str, Any]) -> bool:
        """创建发票申请"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO invoices (invoice_id, order_id, user_id, invoice_title, tax_id, invoice_type, amount, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_data["invoice_id"],
                invoice_data["order_id"],
                invoice_data["user_id"],
                invoice_data["invoice_title"],
                invoice_data.get("tax_id"),
                invoice_data.get("invoice_type", "personal"),
                invoice_data["amount"],
                invoice_data.get("status", "pending")
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[创建发票失败] {str(e)}")
            return False

    def check_order_invoice_eligibility(self, order_id: str) -> Dict[str, Any]:
        """检查订单是否可以开发票"""
        order = self.get_order(order_id)
        if not order:
            return {"eligible": False, "reason": "订单不存在"}

        # 检查订单状态
        if order["status"] not in ["paid", "shipped", "delivered"]:
            return {"eligible": False, "reason": "订单未支付或已取消"}

        # 检查是否已开过发票
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM invoices WHERE order_id = ?", (order_id,))
        existing_invoice = cursor.fetchone()
        conn.close()

        if existing_invoice:
            return {"eligible": False, "reason": "该订单已开具发票"}

        return {"eligible": True, "order": order}


if __name__ == "__main__":
    # 测试数据库功能
    print("=== 数据库管理器测试 ===\n")

    db = DatabaseManager()

    # 测试商品查询
    print("--- 所有商品 ---")
    products = db.get_all_products()
    for p in products:
        print(f"[{p['product_id']}] {p['name']} - ¥{p['price']} (库存: {p['stock']})")

    # 测试商品搜索
    print("\n--- 搜索'耳机' ---")
    results = db.search_products("耳机")
    for p in results:
        print(f"[{p['product_id']}] {p['name']} - {p['description']}")

    # 测试订单查询
    print("\n--- 订单查询 ---")
    order = db.get_order("A1234567890")
    if order:
        print(f"订单号: {order['order_id']}")
        print(f"商品: {order['product_name']}")
        print(f"状态: {order['status']}")
        print(f"物流单号: {order['tracking_number']}")

    # 测试用户订单列表
    print("\n--- 用户U001的订单 ---")
    user_orders = db.get_user_orders("U001")
    for o in user_orders:
        print(f"{o['order_id']} - {o['product_name']} - {o['status']}")

    print("\n测试完成!")
