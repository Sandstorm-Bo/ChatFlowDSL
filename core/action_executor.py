from typing import List, Dict, Any, Optional, Union
import re
import time
from core.database_manager import DatabaseManager
from core.session_manager import Session

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

    def execute(self, actions: List[Dict[str, Any]], session: Union[Session, Dict[str, Any]]) -> List[str]:
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
            elif action_type == "select_product_from_results":
                self._handle_select_product_from_results(action, session)
        
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

    def _handle_api_call(self, action: Dict[str, Any], session: Union[Session, Dict[str, Any]]):
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

        resolved_params = {k: self._resolve_param_value(v, session) for k, v in params.items()}

        # 处理数据库协议
        if endpoint.startswith("database://"):
            data = self._handle_database_query(endpoint, resolved_params, session)
        # 处理传统HTTP API (目前使用Mock)
        else:
            response = self._mock_api.get(endpoint, {})
            data = response.get("data")

        if data is not None:
            self._get_variables(session)[variable_name] = data
            print(f"[ActionExecutor] Saved result to 'session.{variable_name}'")

    def _handle_database_query(self, endpoint: str, params: Dict[str, Any], session: Union[Session, Dict[str, Any]]) -> Any:
        """
        处理数据库查询
        支持的endpoint格式：
        - database://products/list - 获取商品列表
        - database://products/search - 搜索商品
        - database://products/get - 获取商品详情
        - database://orders/get - 获取订单详情
        - database://orders/list - 获取用户订单列表
        - database://refunds/check - 检查退款资格
        - database://invoices/check_eligibility - 检查发票资格
        """
        path = endpoint.replace("database://", "")

        try:
            # 商品相关查询
            if path == "products/list":
                category = params.get("category")
                limit = params.get("limit", 10)
                return self.db.get_all_products(category=category, limit=limit)

            elif path == "products/search":
                # 优先从最近一轮用户输入中提取更“干净”的搜索关键词，避免整句查询命中率低
                raw_keyword = params.get("keyword", "")
                user_input = self._get_session_value(session, "last_user_input", raw_keyword)
                keyword = self._extract_product_search_keyword(user_input, raw_keyword)

                # 从session变量中获取已有关键词作为兜底
                variables = self._get_variables(session)
                if not keyword and "keyword" in variables:
                    keyword = variables["keyword"]

                return self.db.search_products(keyword)

            elif path == "products/get":
                product_id = params.get("product_id")
                variables = self._get_variables(session)
                if not product_id and "product_id" in variables:
                    product_id = variables["product_id"]
                return self.db.get_product(product_id)

            # 订单相关查询
            elif path == "orders/get":
                order_id = params.get("order_id")
                variables = self._get_variables(session)
                if not order_id and "order_id" in variables:
                    order_id = variables["order_id"]
                return self.db.get_order(order_id)

            elif path == "orders/list":
                # 优先从session中获取user_id，实现自动查询当前用户的订单
                user_id = self._get_session_value(session, "user_id")
                if not user_id:
                    user_id = params.get("user_id", "U001")  # 降级到参数或默认用户
                return self.db.get_user_orders(user_id)

            elif path == "orders/search":
                # 根据用户提供的商品关键词、描述信息模糊查询订单
                user_id = self._get_session_value(session, "user_id")
                if not user_id:
                    user_id = params.get("user_id", "U001")

                keyword = params.get("keyword", "")
                if not keyword:
                    variables = self._get_variables(session)
                    keyword = variables.get("order_keyword", "")

                if not keyword:
                    return []

                return self.db.search_user_orders(user_id=user_id, keyword=keyword)

            # 退款相关查询
            elif path == "refunds/check":
                order_id = params.get("order_id")
                variables = self._get_variables(session)
                if not order_id and "order_id" in variables:
                    order_id = variables["order_id"]
                reason_type = params.get("reason_type")
                return self.db.check_refund_eligibility(order_id, reason_type)

            elif path == "refunds/create":
                refund_data = {
                    "refund_id": f"R{int(time.time())}",
                    "order_id": params.get("order_id"),
                    "user_id": params.get("user_id", ""),
                    "reason": params.get("reason"),
                    "reason_type": params.get("reason_type"),
                    "amount": params.get("amount", 0.0),
                    "status": "pending",
                }
                success = self.db.create_refund(refund_data)
                if success:
                    return {"success": True, "message": "退款申请提交成功", "amount": refund_data["amount"]}
                return {"success": False, "message": "退款申请提交失败"}

            # 发票相关查询
            elif path == "invoices/check_eligibility":
                order_id = params.get("order_id")
                variables = self._get_variables(session)
                if not order_id and "order_id" in variables:
                    order_id = variables["order_id"]
                return self.db.check_order_invoice_eligibility(order_id)
            elif path == "invoices/create":
                invoice_data = {
                    "invoice_id": f"I{int(time.time())}",
                    "order_id": params.get("order_id"),
                    "user_id": params.get("user_id", ""),
                    "invoice_title": params.get("title", "个人发票"),
                    "tax_id": params.get("tax_id"),
                    "invoice_type": params.get("invoice_type", "personal"),
                    "amount": params.get("amount", 0.0),
                    "status": "pending",
                }
                success = self.db.create_invoice(invoice_data)
                if success:
                    return {"success": True, "message": "发票申请提交成功", "invoice_id": invoice_data["invoice_id"]}
                return {"success": False, "message": "发票申请提交失败"}

            # 订单写动作
            elif path == "orders/create":
                product_id = params.get("product_id")
                quantity = int(params.get("quantity", 1))
                user_id = self._get_session_value(session, "user_id")
                if not user_id:
                    user_id = params.get("user_id", "U001")
                product = self.db.get_product(product_id)
                if not product:
                    return {"success": False, "message": "商品不存在"}

                order_data = {
                    "order_id": f"A{product_id[-4:]}{int(time.time()) % 10000}",
                    "user_id": user_id,
                    "product_id": product_id,
                    "product_name": product["name"],
                    "quantity": quantity,
                    "total_price": product["price"] * quantity,
                    "status": "paid",
                    "shipping_address": params.get("shipping_address", ""),
                    "tracking_number": "",
                }
                success = self.db.add_order(order_data)
                if success:
                    self.db.decrease_product_stock(product_id, quantity)
                    return {"success": True, "order": order_data}
                return {"success": False, "message": "订单创建失败"}

            elif path == "orders/update_status":
                order_id = params.get("order_id")
                status = params.get("status")
                success = self.db.update_order_status(order_id, status)
                return {"success": success}

            else:
                print(f"[Database Query] Unknown endpoint: {path}")
                return None

        except Exception as e:
            print(f"[Database Query Error] {str(e)}")
            return None


    def _handle_respond(self, action: Dict[str, Any], session: Union[Session, Dict[str, Any]]) -> str:
        """
        处理响应动作，支持复杂的模板渲染
        """
        text = action.get("text", "")
        import re

        # 预处理特殊变量
        self._prepare_display_variables(session)
        display_vars = self._get_display_vars(session)
        variables = self._get_variables(session)

        def repl(match):
            full_match = match.group(0)
            parts_str = match.group(1)  # e.g., "session.product_details.description"
            parts = parts_str.split('.')

            if len(parts) < 2 or parts[0] != 'session':
                return full_match

            # 处理特殊显示变量
            if parts_str in display_vars:
                return display_vars[parts_str]

            # 通用变量访问
            current_data = variables
            for part in parts[1:]:
                if isinstance(current_data, dict):
                    current_data = current_data.get(part)
                else:
                    current_data = None
                    break

            return str(current_data) if current_data is not None else ""

        processed_text = re.sub(r"\{\{\s*(session\..*?)\s*\}\}", repl, text)
        return processed_text

    def _prepare_display_variables(self, session: Union[Session, Dict[str, Any]]):
        """
        准备用于显示的特殊变量
        将复杂数据结构转换为易读的文本格式
        """
        variables = self._get_variables(session)
        display_vars = self._get_display_vars(session)

        # 处理产品列表
        if "featured_products" in variables:
            products = variables["featured_products"]
            if isinstance(products, list) and products:
                product_lines = []
                for p in products:
                    name = p.get("name", "未知商品")
                    price = p.get("price", 0)
                    stock = p.get("stock", 0)
                    product_lines.append(f"• {name} - ¥{price} (库存: {stock})")
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
                # 记录搜索结果数量，供DSL中的条件判断使用
                variables["search_result_count"] = len(results)

                # 如果只有一个结果，自动将其作为当前选中商品，便于后续展示和购买
                if len(results) == 1:
                    variables["current_product"] = results[0]

                if results:
                    result_lines = []
                    for p in results:
                        result_lines.append(f"• {p.get('name')} - ¥{p.get('price')}")
                    display_vars["session.search_result_text"] = f"找到以下商品：\n" + "\n".join(result_lines)
                else:
                    display_vars["session.search_result_text"] = "抱歉，没有找到相关商品。"
    
    # ... _handle_extract_variable and _handle_set_variable remain unchanged
    def _handle_extract_variable(self, action: Dict[str, Any], session: Union[Session, Dict[str, Any]]):
        """Handles the 'extract_variable' action."""
        # This is a simplified version. A real implementation needs access to the last user input.
        # We will simulate it by assuming the input is passed into the session for now.
        user_input = self._get_session_value(session, "last_user_input", "")
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
                self._get_variables(session)[variable_name] = match.group(variable_name)
                print(f"[ActionExecutor] Extracted '{variable_name}' = '{match.group(variable_name)}'")

    def _handle_set_variable(self, action: Dict[str, Any], session: Union[Session, Dict[str, Any]]):
        """Handles the 'set_variable' action."""
        scope = action.get("scope")
        key = action.get("key")
        value = action.get("value")

        if scope == "session" and key:
            self._get_variables(session)[key] = value
            print(f"[ActionExecutor] Set variable '{key}' = '{value}'")

    def _get_variables(self, session: Union[Session, Dict[str, Any]]) -> Dict[str, Any]:
        """Access session variables with write-through semantics."""
        if isinstance(session, Session):
            return session.variables
        return session.setdefault("variables", {})

    def _get_display_vars(self, session: Union[Session, Dict[str, Any]]) -> Dict[str, Any]:
        """Access display variables, creating storage when missing."""
        if isinstance(session, Session):
            if not hasattr(session, "_display_vars"):
                session._display_vars = {}
            return session._display_vars
        return session.setdefault("_display_vars", {})

    def _get_session_value(self, session: Union[Session, Dict[str, Any]], key: str, default: Any = None) -> Any:
        if isinstance(session, Session):
            return getattr(session, key, default)
        return session.get(key, default)

    def _handle_select_product_from_results(self, action: Dict[str, Any], session: Union[Session, Dict[str, Any]]):
        """
        在已有搜索结果列表中，根据用户的自然语言选择具体商品。

        典型输入示例：
        - “平板电脑12”
        - “第一个” / “第二个”
        - “1号那个”
        - “¥2419 的那款”
        """
        variables = self._get_variables(session)
        results = variables.get("search_results") or []
        user_input = str(self._get_session_value(session, "last_user_input", "") or "")

        variables["product_selected"] = False
        if not results or not user_input.strip():
            return

        text = user_input.strip()
        text_lower = text.lower()

        # 1) 尝试根据数字编号或价格选择
        # 1.1 提取所有连续数字
        num_match = re.findall(r"\d+", text)
        chosen = None

        if num_match:
            # 优先尝试数字是否出现在商品名称中（如“平板电脑 12”）
            for num in num_match:
                for p in results:
                    name = str(p.get("name", "") or "")
                    if num in name:
                        chosen = p
                        break
                if chosen:
                    break

            # 其次尝试按“第 N 个”或“编号 N”理解为索引
            if not chosen:
                for num in num_match:
                    try:
                        idx = int(num) - 1
                    except ValueError:
                        continue
                    if 0 <= idx < len(results):
                        chosen = results[idx]
                        break

            # 再次尝试根据价格匹配
            if not chosen:
                for num in num_match:
                    try:
                        price_val = float(num)
                    except ValueError:
                        continue
                    for p in results:
                        price = p.get("price")
                        try:
                            if price is not None and float(price) == price_val:
                                chosen = p
                                break
                        except Exception:
                            continue
                    if chosen:
                        break

        # 2) 根据商品名称关键字进行模糊匹配
        if not chosen:
            tokens = re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]+", text_lower)
            # 去掉明显是数字的 token，避免与索引逻辑重复
            tokens = [t for t in tokens if not t.isdigit()]

            if tokens:
                def score_product(p: Dict[str, Any]) -> int:
                    name = str(p.get("name", "") or "").lower()
                    s = 0
                    for t in tokens:
                        if t and t in name:
                            s += len(t)
                    return s

                scored = [(score_product(p), p) for p in results]
                scored.sort(key=lambda x: x[0], reverse=True)
                if scored and scored[0][0] > 0:
                    chosen = scored[0][1]

        if chosen is not None:
            variables["current_product"] = chosen
            variables["product_selected"] = True
            print(f"[ActionExecutor] Selected product from results: {chosen.get('name')}")
        else:
            print("[ActionExecutor] No product matched from search_results using user input")

    def _extract_product_search_keyword(self, user_input: str, fallback: str = "") -> str:
        """
        从用户原始输入中尽量提取出用于商品搜索的简短关键词。

        优先匹配常见商品词，其次根据中文/英文 token 做简单启发式截取。
        """
        text = (user_input or "").strip()
        if not text:
            return fallback

        # 常见商品关键词词表（可根据需要扩充）
        vocab = [
            "平板电脑", "平板", "笔记本", "轻薄本",
            "无线蓝牙耳机", "蓝牙耳机", "耳机",
            "智能手环", "手环",
            "充电宝", "移动电源",
            "机械键盘", "键盘",
            "网络摄像头", "摄像头",
            "显示器", "电竞显示器",
            "扩展坞",
            "智能音箱", "音箱",
            "游戏鼠标", "鼠标",
        ]

        hits = [w for w in vocab if w in text]
        if hits:
            # 命中多个时优先选择最长的词
            hits.sort(key=len, reverse=True)
            return hits[0]

        # 否则按中英文/数字切分，取最后一个 token 作为候选
        tokens = re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]+", text)
        if not tokens:
            return fallback or text

        candidate = tokens[-1]

        # 对特别长的中文 token，截取末尾几位，尽量保留商品名核心部分
        if len(candidate) > 6 and any("\u4e00" <= ch <= "\u9fff" for ch in candidate):
            candidate = candidate[-4:]

        return candidate or fallback or text

    def _resolve_param_value(self, value: Any, session: Union[Session, Dict[str, Any]]) -> Any:
        """Resolve templated parameter values using session variables."""
        if isinstance(value, str):
            match = re.match(r"\{\{\s*session\.(.*?)\s*\}\}", value)
            if match:
                current = self._get_variables(session)
                for part in match.group(1).split('.'):
                    if isinstance(current, dict):
                        current = current.get(part)
                    else:
                        current = None
                        break
                return current
        return value
