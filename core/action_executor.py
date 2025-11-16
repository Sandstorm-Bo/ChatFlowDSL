from typing import List, Dict, Any, Optional
import re
from core.database_manager import DatabaseManager

class ActionExecutor:
    """
    动作执行器
    执行DSL中定义的各种动作，并与数据库集成
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        初始化动作执行器

        Args:
            db_manager: 数据库管理器实例，如果为None则自动创建
        """
        self.db = db_manager if db_manager else DatabaseManager()

        # 保留Mock API作为降级方案
        self._mock_api = {
            "https://api.my-shop.com/products/featured": {
                "data": [
                    {"id": "headset_001", "name": "智能降噪耳机"},
                    {"id": "powerbank_002", "name": "超长续航移动电源"}
                ]
            },
            "https://api.my-shop.com/products/headset_001": {
                "data": {
                    "description": "采用业界领先的主动降噪技术，配合长达20小时的播放时间，是您通勤和旅行的理想伴侣。",
                    "price": 1299
                }
            },
            "https://api.my-shop.com/products/powerbank_002": {
                "data": {
                    "description": "拥有20000mAh大容量，支持双向快充，可以同时为三台设备充电，确保您的设备时刻在线。",
                    "price": 299
                }
            }
        }

    def execute(self, actions: List[Dict[str, Any]], session: Dict[str, Any]) -> List[str]:
        """
        Executes a list of actions and returns a list of text responses for the user.
        """
        responses = []
        # We need to handle data-changing actions first (like api_call)
        # so that subsequent respond actions can use the data.
        for action in actions:
            action_type = action.get("type")
            if action_type == "api_call":
                self._handle_api_call(action, session)
            elif action_type == "extract_variable":
                self._handle_extract_variable(action, session)
            elif action_type == "set_variable":
                self._handle_set_variable(action, session)
        
        # Then, handle actions that generate responses
        for action in actions:
            action_type = action.get("type")
            if action_type == "respond":
                response_text = self._handle_respond(action, session)
                if response_text:
                    responses.append(response_text)
            elif action_type not in ["api_call", "extract_variable", "set_variable", "wait_for_input"]:
                 print(f"Warning: Unknown action type '{action_type}'")

        return responses

    def _handle_api_call(self, action: Dict[str, Any], session: Dict[str, Any]):
        """
        处理API调用动作
        支持database://协议直接查询数据库，或使用传统HTTP API
        """
        endpoint = action.get("endpoint", action.get("url", ""))
        save_to = action.get("save_to")
        params = action.get("params", {})

        if not save_to or not save_to.startswith("session."):
            return

        variable_name = save_to.split('.')[1]

        print(f"[ActionExecutor] Calling API: {endpoint}")

        # 处理数据库协议
        if endpoint.startswith("database://"):
            data = self._handle_database_query(endpoint, params, session)
        # 处理传统HTTP API (目前使用Mock)
        else:
            response = self._mock_api.get(endpoint, {})
            data = response.get("data")

        if data is not None:
            session.setdefault("variables", {})[variable_name] = data
            print(f"[ActionExecutor] Saved result to 'session.{variable_name}'")

    def _handle_database_query(self, endpoint: str, params: Dict[str, Any], session: Dict[str, Any]) -> Any:
        """
        处理数据库查询
        支持的endpoint格式：
        - database://products/list - 获取商品列表
        - database://products/search - 搜索商品
        - database://products/get - 获取商品详情
        - database://orders/get - 获取订单详情
        - database://orders/list - 获取用户订单列表
        - database://refunds/check - 检查退款状态
        - database://invoices/check - 检查发票资格
        """
        path = endpoint.replace("database://", "")

        try:
            # 商品相关查询
            if path == "products/list":
                category = params.get("category")
                limit = params.get("limit", 10)
                return self.db.get_all_products(category=category, limit=limit)

            elif path == "products/search":
                keyword = params.get("keyword", "")
                # 从session变量中获取关键词
                if not keyword and "keyword" in session.get("variables", {}):
                    keyword = session["variables"]["keyword"]
                return self.db.search_products(keyword)

            elif path == "products/get":
                product_id = params.get("product_id")
                if not product_id and "product_id" in session.get("variables", {}):
                    product_id = session["variables"]["product_id"]
                return self.db.get_product(product_id)

            # 订单相关查询
            elif path == "orders/get":
                order_id = params.get("order_id")
                if not order_id and "order_id" in session.get("variables", {}):
                    order_id = session["variables"]["order_id"]
                return self.db.get_order(order_id)

            elif path == "orders/list":
                # 优先从session中获取user_id，实现自动查询当前用户的订单
                user_id = session.get("user_id")
                if not user_id:
                    user_id = params.get("user_id", "U001")  # 降级到参数或默认用户
                return self.db.get_user_orders(user_id)

            # 退款相关查询
            elif path == "refunds/check":
                order_id = params.get("order_id")
                if not order_id and "order_id" in session.get("variables", {}):
                    order_id = session["variables"]["order_id"]
                return self.db.get_refund_by_order(order_id)

            # 发票相关查询
            elif path == "invoices/check_eligibility":
                order_id = params.get("order_id")
                if not order_id and "order_id" in session.get("variables", {}):
                    order_id = session["variables"]["order_id"]
                return self.db.check_order_invoice_eligibility(order_id)

            else:
                print(f"[Database Query] Unknown endpoint: {path}")
                return None

        except Exception as e:
            print(f"[Database Query Error] {str(e)}")
            return None


    def _handle_respond(self, action: Dict[str, Any], session: Dict[str, Any]) -> str:
        """
        处理响应动作，支持复杂的模板渲染
        """
        text = action.get("text", "")
        import re

        # 预处理特殊变量
        self._prepare_display_variables(session)

        def repl(match):
            full_match = match.group(0)
            parts_str = match.group(1)  # e.g., "session.product_details.description"
            parts = parts_str.split('.')

            if len(parts) < 2 or parts[0] != 'session':
                return full_match

            # 处理特殊显示变量
            if parts_str in session.get("_display_vars", {}):
                return session["_display_vars"][parts_str]

            # 通用变量访问
            current_data = session.get("variables", {})
            for part in parts[1:]:
                if isinstance(current_data, dict):
                    current_data = current_data.get(part)
                else:
                    current_data = None
                    break

            return str(current_data) if current_data is not None else ""

        processed_text = re.sub(r"\{\{\s*(session\..*?)\s*\}\}", repl, text)
        return processed_text

    def _prepare_display_variables(self, session: Dict[str, Any]):
        """
        准备用于显示的特殊变量
        将复杂数据结构转换为易读的文本格式
        """
        variables = session.get("variables", {})
        display_vars = session.setdefault("_display_vars", {})

        # 处理产品列表
        if "featured_products" in variables:
            products = variables["featured_products"]
            if isinstance(products, list) and products:
                # 生成产品列表文本
                product_lines = []
                for idx, p in enumerate(products, 1):
                    name = p.get("name", "未知商品")
                    price = p.get("price", 0)
                    stock = p.get("stock", 0)
                    product_lines.append(f"{idx}. {name} - ¥{price} (库存: {stock})")
                display_vars["session.products_list"] = "\n".join(product_lines)
                display_vars["session.featured_products_names"] = "、".join([p.get("name", "") for p in products])

        # 处理当前产品
        if "current_product" in variables:
            product = variables["current_product"]
            if isinstance(product, dict):
                # 格式化特性列表
                features = product.get("features")
                if isinstance(features, list):
                    display_vars["session.current_product.features"] = "\n".join([f"• {f}" for f in features])

        # 处理订单状态
        if "current_order" in variables:
            order = variables["current_order"]
            if isinstance(order, dict):
                status = order.get("status", "unknown")
                status_map = {
                    "pending": "待付款",
                    "paid": "已付款，待发货",
                    "shipped": "已发货",
                    "delivered": "已送达",
                    "cancelled": "已取消"
                }
                display_vars["session.order_status_text"] = status_map.get(status, status)

                # 物流信息
                tracking = order.get("tracking_number", "")
                if tracking:
                    display_vars["session.tracking_info"] = f"物流单号：{tracking}"
                else:
                    display_vars["session.tracking_info"] = ""

        # 处理订单列表
        if "user_orders" in variables:
            orders = variables["user_orders"]
            if isinstance(orders, list) and orders:
                order_lines = []
                for order in orders:
                    order_id = order.get("order_id", "")
                    product_name = order.get("product_name", "")
                    status = order.get("status", "")
                    status_map = {
                        "pending": "待付款",
                        "paid": "已付款",
                        "shipped": "已发货",
                        "delivered": "已送达",
                        "cancelled": "已取消"
                    }
                    status_text = status_map.get(status, status)
                    order_lines.append(f"• {order_id} - {product_name} [{status_text}]")
                display_vars["session.order_list_text"] = "\n".join(order_lines)
            else:
                display_vars["session.order_list_text"] = "暂无订单记录"

        # 处理搜索结果
        if "search_results" in variables:
            results = variables["search_results"]
            if isinstance(results, list):
                if results:
                    result_lines = []
                    for idx, p in enumerate(results, 1):
                        result_lines.append(f"{idx}. {p.get('name')} - ¥{p.get('price')}")
                    display_vars["session.search_result_text"] = f"找到以下商品：\n" + "\n".join(result_lines)
                else:
                    display_vars["session.search_result_text"] = "抱歉，没有找到相关商品。"
    
    # ... _handle_extract_variable and _handle_set_variable remain unchanged
    def _handle_extract_variable(self, action: Dict[str, Any], session: Dict[str, Any]):
        """Handles the 'extract_variable' action."""
        # This is a simplified version. A real implementation needs access to the last user input.
        # We will simulate it by assuming the input is passed into the session for now.
        user_input = session.get("last_user_input", "")
        regex = action.get("regex")
        target_variable_path = action.get("target")

        if not regex or not target_variable_path or not target_variable_path.startswith("session."):
            return

        match = re.search(regex, user_input)
        if match:
            # Assumes the regex has a named group corresponding to the variable name
            # e.g., (?P<order_id>...) and target is "session.order_id"
            variable_name = target_variable_path.split('.')[1]
            if variable_name in match.groupdict():
                session.setdefault("variables", {})[variable_name] = match.group(variable_name)
                print(f"[ActionExecutor] Extracted '{variable_name}' = '{match.group(variable_name)}'")

    def _handle_set_variable(self, action: Dict[str, Any], session: Dict[str, Any]):
        """Handles the 'set_variable' action."""
        scope = action.get("scope")
        key = action.get("key")
        value = action.get("value")

        if scope == "session" and key:
            session.setdefault("variables", {})[key] = value
            print(f"[ActionExecutor] Set variable '{key}' = '{value}'")
