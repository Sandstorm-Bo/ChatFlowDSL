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

        # 用户表（增加了密码字段用于登录认证）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                address TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_login TEXT
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

        # 添加测试用户（包含密码）
        self.add_user({
            "user_id": "U001",
            "username": "张三",
            "password": "password123",
            "phone": "13800138000",
            "email": "zhangsan@example.com",
            "address": "北京市朝阳区xx街道xx号"
        })

        self.add_user({
            "user_id": "U002",
            "username": "李四",
            "password": "password456",
            "phone": "13900139000",
            "email": "lisi@example.com",
            "address": "上海市浦东新区xx路xx号"
        })

        self.add_user({
            "user_id": "U003",
            "username": "王五",
            "password": "password789",
            "phone": "13700137000",
            "email": "wangwu@example.com",
            "address": "广州市天河区xx大道xx号"
        })

        # 添加测试商品 - 生成至少50款不同商品
        base_catalog = [
            {
                "name_prefix": "无线蓝牙耳机",
                "category": "数码配件",
                "base_price": 269.0,
                "description": "高品质无线蓝牙耳机，兼顾通勤与运动场景。",
                "features": ["主动降噪", "30小时续航", "Type-C快充", "佩戴舒适贴合"],
                "image_prefix": "headset"
            },
            {
                "name_prefix": "智能手环",
                "category": "智能穿戴",
                "base_price": 199.0,
                "description": "轻巧的健康管家，支持全天候健康监测。",
                "features": ["心率监测", "血氧跟踪", "50米防水", "消息提醒"],
                "image_prefix": "band"
            },
            {
                "name_prefix": "便携充电宝",
                "category": "数码配件",
                "base_price": 149.0,
                "description": "大容量双向快充移动电源，随时补能。",
                "features": ["20000mAh", "双向快充", "多设备同充", "LED电量显示"],
                "image_prefix": "powerbank"
            },
            {
                "name_prefix": "机械键盘",
                "category": "电脑外设",
                "base_price": 399.0,
                "description": "专业机械键盘，游戏与办公手感兼备。",
                "features": ["热插拔轴体", "RGB背光", "宏按键", "全键无冲"],
                "image_prefix": "keyboard"
            },
            {
                "name_prefix": "4K网络摄像头",
                "category": "电脑外设",
                "base_price": 569.0,
                "description": "馈送清晰画质的视频会议摄像头。",
                "features": ["4K超清", "自动对焦", "降噪麦克风", "广角镜头"],
                "image_prefix": "webcam"
            },
            {
                "name_prefix": "运动蓝牙耳机",
                "category": "智能穿戴",
                "base_price": 259.0,
                "description": "专为运动设计的稳固挂耳式蓝牙耳机。",
                "features": ["防汗防水", "低延迟", "稳固挂耳设计", "语音助手"],
                "image_prefix": "sport_earbud"
            },
            {
                "name_prefix": "专业游戏鼠标",
                "category": "电脑外设",
                "base_price": 269.0,
                "description": "高精度电竞鼠标，适合 FPS/MOBA 用户。",
                "features": ["16000DPI", "可编程按键", "RGB灯效", "宏功能"],
                "image_prefix": "mouse"
            },
            {
                "name_prefix": "电竞显示器",
                "category": "电脑外设",
                "base_price": 1299.0,
                "description": "2K 高刷新率电竞显示器，游戏画面流畅。",
                "features": ["165Hz高刷", "1ms响应", "HDR支持", "低蓝光护眼"],
                "image_prefix": "monitor"
            },
            {
                "name_prefix": "USB-C多功能扩展坞",
                "category": "数码配件",
                "base_price": 329.0,
                "description": "一线连接笔记本，扩展多种实用接口。",
                "features": ["HDMI 4K输出", "千兆网口", "USB 3.0 x3", "PD快充"],
                "image_prefix": "hub"
            },
            {
                "name_prefix": "智能音箱",
                "category": "智能家居",
                "base_price": 199.0,
                "description": "支持语音助手和智能家居联动的小型音箱。",
                "features": ["远场拾音", "语音唤醒", "云端音乐库", "IoT控制"],
                "image_prefix": "speaker"
            },
            {
                "name_prefix": "高性能轻薄本",
                "category": "电脑整机",
                "base_price": 5899.0,
                "description": "全金属轻薄本，移动办公与创作兼顾。",
                "features": ["12代酷睿", "16GB内存", "512GB SSD", "全功能接口"],
                "image_prefix": "laptop"
            },
            {
                "name_prefix": "平板电脑",
                "category": "平板电脑",
                "base_price": 2399.0,
                "description": "支持手写笔与键盘扩展的多任务平板。",
                "features": ["2K全面屏", "四扬声器", "手写笔支持", "分屏多任务"],
                "image_prefix": "tablet"
            },
            {
                "name_prefix": "智能家居中枢",
                "category": "智能家居",
                "base_price": 799.0,
                "description": "统一管理家中智能设备的控制中枢。",
                "features": ["Zigbee网关", "自动化流程", "摄像头接入", "安全检测"],
                "image_prefix": "homehub"
            },
            {
                "name_prefix": "扫地机器人",
                "category": "智能家居",
                "base_price": 1599.0,
                "description": "自动规划路径的扫拖一体机器人。",
                "features": ["激光导航", "扫拖一体", "自动回充", "语音控制"],
                "image_prefix": "robotvac"
            }
        ]

        products = []
        for idx in range(1, 51):
            template = base_catalog[(idx - 1) % len(base_catalog)]
            price = template["base_price"] + (idx % 5) * 10
            stock = 80 + (idx * 7) % 220
            product = {
                "product_id": f"P{idx:03d}",
                "name": f"{template['name_prefix']} {idx}",
                "category": template["category"],
                "price": round(price, 2),
                "stock": stock,
                "description": template["description"],
                "features": json.dumps(template["features"], ensure_ascii=False),
                "image_url": f"https://example.com/images/{template['image_prefix']}_{idx}.jpg"
            }
            products.append(product)

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
                INSERT INTO users (user_id, username, password, phone, email, address)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_data["user_id"],
                user_data["username"],
                user_data["password"],
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

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        用户登录认证

        Args:
            username: 用户名
            password: 密码

        Returns:
            如果认证成功，返回用户信息（不含密码）；否则返回None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        row = cursor.fetchone()

        if row:
            user_data = dict(row)
            # 更新最后登录时间
            cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = ?", (user_data["user_id"],))
            conn.commit()
            # 移除密码字段，不返回给客户端
            user_data.pop("password", None)
            conn.close()
            return user_data

        conn.close()
        return None

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        根据用户名获取用户信息

        Args:
            username: 用户名

        Returns:
            用户信息（包含密码字段）
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def register_user(self, username: str, password: str, phone: str = None, email: str = None, address: str = None) -> Dict[str, Any]:
        """
        用户注册

        Args:
            username: 用户名（必须唯一）
            password: 密码
            phone: 手机号（可选）
            email: 邮箱（可选）
            address: 地址（可选）

        Returns:
            成功返回 {"success": True, "user_id": "...", "message": "..."}
            失败返回 {"success": False, "message": "错误信息"}
        """
        # 检查用户名是否已存在
        existing_user = self.get_user_by_username(username)
        if existing_user:
            return {
                "success": False,
                "message": f"用户名 '{username}' 已被注册，请使用其他用户名"
            }

        # 生成新的user_id
        import uuid
        user_id = f"U{str(uuid.uuid4())[:8].upper()}"

        # 确保user_id唯一（极小概率会重复）
        while self.get_user(user_id):
            user_id = f"U{str(uuid.uuid4())[:8].upper()}"

        # 添加用户
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (user_id, username, password, phone, email, address)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, username, password, phone, email, address))
            conn.commit()
            conn.close()

            return {
                "success": True,
                "user_id": user_id,
                "message": f"注册成功！欢迎您，{username}！"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"注册失败: {str(e)}"
            }

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

    def decrease_product_stock(self, product_id: str, amount: int = 1) -> bool:
        """减少指定商品库存"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE products
                SET stock = stock - ?
                WHERE product_id = ? AND stock >= ?
                """,
                (amount, product_id, amount),
            )
            affected = cursor.rowcount
            conn.commit()
            conn.close()
            return affected > 0
        except Exception as e:
            print(f"[更新库存失败] {str(e)}")
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

    def search_user_orders(self, user_id: str, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        按商品名称关键字模糊查询用户订单

        Args:
            user_id: 用户ID
            keyword: 关键字（例如“水杯”“马克杯”“耳机”等）
            limit: 返回的最大订单数
        """
        if not keyword:
            return []

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM orders
            WHERE user_id = ? AND product_name LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, f"%{keyword}%", limit),
        )
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
        """根据订单号查询最新一条退款记录"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM refunds WHERE order_id = ? ORDER BY created_at DESC LIMIT 1",
            (order_id,),
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def check_refund_eligibility(
        self, order_id: str, reason_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        检查订单是否符合退款申请条件

        返回字典示例:
        {
            "eligible": True/False,
            "amount": 299.0,          # 可退金额（如适用）
            "order": {...},           # 订单信息（如存在）
            "reason": "订单不存在",     # 机器可读原因
            "message": "抱歉，订单不存在，无法申请退款"  # 用户可读提示
        }
        """
        order = self.get_order(order_id)
        if not order:
            return {
                "eligible": False,
                "reason": "订单不存在",
                "message": "抱歉，没有找到该订单，无法为您办理退款。",
            }

        # 示例规则：只有已付款及之后状态可以申请退款
        if order["status"] not in ["paid", "shipped", "delivered"]:
            return {
                "eligible": False,
                "order": order,
                "reason": "订单未支付或已取消",
                "message": "当前订单未支付或已取消，无法发起退款申请。",
            }

        # 如果已存在退款记录且状态为进行中/完成，则不允许重复申请
        existing = self.get_refund_by_order(order_id)
        if existing and existing.get("status") in ["pending", "approved", "completed"]:
            return {
                "eligible": False,
                "order": order,
                "reason": "已有退款记录",
                "message": "该订单已存在退款记录，请勿重复申请。",
            }

        # 默认可退金额为订单总价（更复杂的规则可根据reason_type扩展）
        amount = order.get("total_price", 0.0)
        return {
            "eligible": True,
            "order": order,
            "amount": amount,
            "reason": "符合退款条件",
            "message": "该订单符合退款条件，我可以为您提交退款申请。",
        }

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
            return {
                "eligible": False,
                "reason": "订单不存在",
                "message": "抱歉，没有找到该订单，无法开具发票。",
            }

        # 检查订单状态
        if order["status"] not in ["paid", "shipped", "delivered"]:
            return {
                "eligible": False,
                "reason": "订单未支付或已取消",
                "message": "订单未支付或已取消，暂时无法开具发票。",
            }

        # 检查是否已开过发票
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM invoices WHERE order_id = ?", (order_id,))
        existing_invoice = cursor.fetchone()
        conn.close()

        if existing_invoice:
            return {
                "eligible": False,
                "reason": "该订单已开具发票",
                "message": "该订单已开具发票，如需修改请联系人工客服。",
            }

        return {
            "eligible": True,
            "order": order,
            "message": "该订单符合开票条件，我可以为您提交发票申请。",
        }


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
