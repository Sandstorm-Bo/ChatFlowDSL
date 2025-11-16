from typing import Dict, Any, Optional, List
from openai import OpenAI
import json
import re

## LLM意图识别器
class LLMResponder:
    """
    LLM响应器，支持OpenAI兼容接口
    功能：
    1. 意图识别：识别用户的意图类型
    2. 实体提取：从用户输入中提取关键信息
    3. 智能回复：生成自然语言响应
    """

    def __init__(self, api_key: str, model_name: str, base_url: Optional[str] = None, timeout: float = 10.0):
        """
        初始化LLM响应器

        Args:
            api_key: API密钥
            model_name: 模型名称（如 gpt-3.5-turbo）
            base_url: 自定义API基础URL（用于兼容其他OpenAI格式API）
            timeout: API调用超时时间（秒），默认10秒
        """
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url
        self.timeout = timeout

        # 配置OpenAI客户端（使用新版API）
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )

    def recognize_intent(self, user_input: str, available_intents: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        识别用户输入的意图

        Args:
            user_input: 用户输入文本
            available_intents: 可选的意图列表，帮助模型更准确地分类

        Returns:
            包含意图和置信度的字典：
            {
                "intent": "查询订单",
                "confidence": 0.95,
                "entities": {"order_id": "A1234567890"}
            }
        """
        # 构建提示词
        intent_list = "\n".join([f"- {intent}" for intent in (available_intents or [])])

        system_prompt = """你是一个智能客服机器人的意图识别系统。
你的任务是分析用户输入，识别用户的意图类型。

常见意图类型包括：
- 产品咨询：用户想了解产品信息、功能、价格等
- 订单查询：用户想查看订单状态、物流信息
- 退款退货：用户想申请退款或退货
- 发票申请：用户需要开具发票
- 故障报修：用户反馈产品问题或故障
- 闲聊问候：普通的打招呼或闲聊

请以JSON格式返回结果，包含以下字段：
{
    "intent": "意图类型",
    "confidence": 0.0-1.0的置信度,
    "entities": {"实体类型": "实体值"},
    "reasoning": "简短的判断理由"
}

例如：
用户输入："我想查一下订单A1234567890的物流"
返回：{"intent": "订单查询", "confidence": 0.95, "entities": {"order_id": "A1234567890"}, "reasoning": "用户明确提到查询订单和物流信息"}
"""

        user_prompt = f"用户输入：{user_input}\n\n请分析用户意图。"

        try:
            # 调用OpenAI API（使用新版客户端）
            print(f"\n{'='*60}")
            print(f"[LLM API 调用 DEBUG]")
            print(f"{'='*60}")
            print(f"  Base URL: {self.base_url}")
            print(f"  Model: {self.model_name}")
            print(f"  API Key: {self.api_key[:15]}...{self.api_key[-5:] if len(self.api_key) > 20 else '(too short)'}")
            print(f"  Timeout: {self.timeout}秒")
            print(f"  User Input: {user_input}")
            print(f"  正在调用 API...")

            import time
            start_time = time.time()

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # 较低的温度以获得更确定的结果
                max_tokens=200,
                timeout=self.timeout
            )

            elapsed = time.time() - start_time
            print(f"  ✓ API 调用成功! 耗时: {elapsed:.2f}秒")
            print(f"{'='*60}\n")

            # 解析响应
            content = response.choices[0].message.content.strip()

            # 尝试提取JSON
            result = self._extract_json(content)

            if result:
                return result
            else:
                # 如果无法解析JSON，返回默认结果
                return {
                    "intent": "未知",
                    "confidence": 0.3,
                    "entities": {},
                    "reasoning": "无法解析LLM响应"
                }

        except Exception as e:
            print(f"\n{'='*60}")
            print(f"[LLM API 调用失败]")
            print(f"{'='*60}")
            print(f"  错误类型: {type(e).__name__}")
            print(f"  错误信息: {str(e)}")

            # 详细错误诊断
            if "401" in str(e) or "Unauthorized" in str(e):
                print(f"  诊断: API Key 无效或未授权")
                print(f"  建议: 检查 API Key 是否正确，是否有权限访问模型")
            elif "timeout" in str(e).lower():
                print(f"  诊断: 请求超时")
                print(f"  建议: 检查网络连接，或增加 timeout 参数")
            elif "connection" in str(e).lower():
                print(f"  诊断: 网络连接失败")
                print(f"  建议: 检查 base_url 是否正确，网络是否通畅")
            else:
                print(f"  建议: 查看完整错误堆栈")

            print(f"{'='*60}\n")

            # 降级到规则匹配
            return self._fallback_intent_recognition(user_input)

    def _extract_json(self, text: str) -> Optional[Dict]:
        """从文本中提取JSON对象"""
        try:
            # 尝试直接解析
            return json.loads(text)
        except:
            # 尝试查找JSON代码块
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except:
                    pass

            # 尝试查找任何JSON对象
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except:
                    pass

        return None

    def _fallback_intent_recognition(self, user_input: str) -> Dict[str, Any]:
        """
        降级方案：基于规则的意图识别
        当API调用失败时使用
        """
        print(f"[使用降级规则匹配] 输入: '{user_input}'")

        # 规则库
        rules = [
            {
                "patterns": ["产品", "商品", "介绍", "功能", "价格", "推荐", "有什么"],
                "intent": "产品咨询",
                "confidence": 0.8
            },
            {
                "patterns": ["订单", "物流", "快递", "发货", "到哪", "查询订单"],
                "intent": "订单查询",
                "confidence": 0.85
            },
            {
                "patterns": ["退款", "退货", "退", "不想要", "质量问题"],
                "intent": "退款退货",
                "confidence": 0.9
            },
            {
                "patterns": ["发票", "invoice", "开票", "抬头", "税号"],
                "intent": "发票申请",
                "confidence": 0.9
            },
            {
                "patterns": ["坏了", "故障", "问题", "修", "不能用", "没声音", "连不上"],
                "intent": "故障报修",
                "confidence": 0.85
            },
            {
                "patterns": ["你好", "您好", "hi", "hello", "在吗"],
                "intent": "闲聊问候",
                "confidence": 0.95
            }
        ]

        # 提取订单号
        order_id_match = re.search(r'[A-Z]\d{10}', user_input)
        entities = {}
        if order_id_match:
            entities["order_id"] = order_id_match.group(0)

        # 匹配规则
        for rule in rules:
            for pattern in rule["patterns"]:
                if pattern in user_input:
                    return {
                        "intent": rule["intent"],
                        "confidence": rule["confidence"],
                        "entities": entities,
                        "reasoning": f"匹配到关键词: {pattern}"
                    }

        # 默认意图
        return {
            "intent": "未知",
            "confidence": 0.3,
            "entities": entities,
            "reasoning": "未匹配到任何已知模式"
        }

    def extract_entities(self, user_input: str, entity_types: List[str]) -> Dict[str, Any]:
        """
        从用户输入中提取指定类型的实体

        Args:
            user_input: 用户输入
            entity_types: 需要提取的实体类型列表，如 ["订单号", "产品名称", "金额"]

        Returns:
            提取的实体字典
        """
        system_prompt = f"""你是一个实体提取系统。
从用户输入中提取以下类型的实体：{', '.join(entity_types)}

以JSON格式返回结果，格式为：
{{"实体类型": "实体值", ...}}

如果某个实体不存在，则不包含在结果中。
"""

        user_prompt = f"用户输入：{user_input}"

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=100,
                timeout=self.timeout
            )

            content = response.choices[0].message.content.strip()
            result = self._extract_json(content)
            return result if result else {}

        except Exception as e:
            print(f"[实体提取失败] {str(e)}")
            return {}

    def check_semantic_match(self, user_input: str, semantic_meaning: str,
                            session_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        检查用户输入是否符合指定的语义含义（用于条件判断）

        Args:
            user_input: 用户输入文本
            semantic_meaning: 期望的语义含义描述
            session_context: 会话上下文（可选，提供更准确的判断）

        Returns:
            {
                "matched": True/False,
                "confidence": 0.0-1.0,
                "reasoning": "判断理由"
            }
        """
        # 构建上下文信息
        context_info = ""
        if session_context:
            context_info = f"\n\n当前会话上下文：{json.dumps(session_context, ensure_ascii=False, indent=2)}"

        system_prompt = f"""你是一个语义理解系统。
你的任务是判断用户输入是否符合指定的语义含义。

请以JSON格式返回结果：
{{
    "matched": true/false,
    "confidence": 0.0-1.0的置信度,
    "reasoning": "简短的判断理由"
}}

判断标准：
- matched为true表示用户输入符合语义含义
- confidence表示判断的置信度（0-1之间）
- 置信度>=0.7才认为是明确匹配
"""

        user_prompt = f"""用户输入：{user_input}

期望的语义含义：{semantic_meaning}{context_info}

请判断用户输入是否符合这个语义含义。"""

        try:
            print(f"[LLM语义匹配] 输入: '{user_input}' | 期望语义: '{semantic_meaning}'")

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,  # 低温度以获得更一致的判断
                max_tokens=150,
                timeout=self.timeout
            )

            content = response.choices[0].message.content.strip()
            result = self._extract_json(content)

            if result and "matched" in result:
                print(f"  ✓ LLM判断: {'匹配' if result['matched'] else '不匹配'} (置信度: {result.get('confidence', 0):.2f})")
                return result
            else:
                return {
                    "matched": False,
                    "confidence": 0.0,
                    "reasoning": "无法解析LLM响应"
                }

        except Exception as e:
            print(f"[LLM语义匹配失败] {type(e).__name__}: {str(e)}")
            # 失败时返回不匹配
            return {
                "matched": False,
                "confidence": 0.0,
                "reasoning": f"API调用失败: {str(e)}"
            }

    def match_condition_with_llm(self, user_input: str, condition_description: str,
                                 available_targets: List[str],
                                 session_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        使用LLM进行多路条件匹配（用于状态转换）

        Args:
            user_input: 用户输入
            condition_description: 当前状态的描述
            available_targets: 可选的目标状态列表及其触发条件描述
            session_context: 会话上下文

        Returns:
            {
                "target": "目标状态",
                "confidence": 0.0-1.0,
                "reasoning": "匹配理由"
            }
        """
        context_info = ""
        if session_context:
            # 只包含关键上下文信息，避免过长
            key_context = {
                "current_state": session_context.get("current_state_id"),
                "variables": session_context.get("variables", {})
            }
            context_info = f"\n\n当前会话上下文：{json.dumps(key_context, ensure_ascii=False, indent=2)}"

        targets_info = "\n".join([f"- {target}" for target in available_targets])

        system_prompt = f"""你是一个对话流程路由系统。
你的任务是根据用户输入和当前状态，判断应该转换到哪个目标状态。

当前状态：{condition_description}

可选的目标状态：
{targets_info}

请以JSON格式返回结果：
{{
    "target": "目标状态名称",
    "confidence": 0.0-1.0的置信度,
    "reasoning": "选择理由"
}}

如果没有合适的目标，返回：
{{
    "target": null,
    "confidence": 0.0,
    "reasoning": "无匹配目标"
}}
"""

        user_prompt = f"用户输入：{user_input}{context_info}\n\n请判断应该转换到哪个目标状态。"

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=200,
                timeout=self.timeout
            )

            content = response.choices[0].message.content.strip()
            result = self._extract_json(content)

            if result:
                return result
            else:
                return {
                    "target": None,
                    "confidence": 0.0,
                    "reasoning": "无法解析LLM响应"
                }

        except Exception as e:
            print(f"[LLM条件匹配失败] {str(e)}")
            return {
                "target": None,
                "confidence": 0.0,
                "reasoning": f"API调用失败: {str(e)}"
            }

    def generate_response(self, context: str, user_input: str) -> str:
        """
        生成智能回复

        Args:
            context: 对话上下文
            user_input: 用户输入

        Returns:
            生成的回复文本
        """
        system_prompt = """你是一个智能客服机器人。
请根据对话上下文和用户输入，生成友好、专业的回复。
回复要求：
- 简洁明了，不超过100字
- 语气友好、礼貌
- 针对用户问题给出具体建议
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "assistant", "content": context},
            {"role": "user", "content": user_input}
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=150,
                timeout=self.timeout
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"[回复生成失败] {str(e)}")
            return "抱歉，我暂时无法理解您的问题，请您稍后再试或联系人工客服。"


if __name__ == '__main__':
    # 示例用法
    print("=== LLM响应器测试 ===\n")

    # 使用环境变量或配置文件中的API密钥
    import os
    api_key = os.getenv("OPENAI_API_KEY", "test_key")

    responder = LLMResponder(
        api_key=api_key,
        model_name="gpt-3.5-turbo",
        base_url=None  # 或设置为其他兼容OpenAI的API端点
    )

    # 测试意图识别
    test_inputs = [
        "你好，我想了解一下你们的产品",
        "我的订单A1234567890到哪里了？",
        "我想退款，这个产品有质量问题",
        "能帮我开个发票吗？",
        "我的耳机连不上蓝牙了"
    ]

    print("--- 意图识别测试 ---")
    for text in test_inputs:
        result = responder.recognize_intent(text)
        print(f"\n用户输入: '{text}'")
        print(f"识别结果: {json.dumps(result, ensure_ascii=False, indent=2)}")

    # 测试实体提取
    print("\n\n--- 实体提取测试 ---")
    text = "我要退订单A1234567890，退款金额是299元"
    entities = responder.extract_entities(text, ["订单号", "金额"])
    print(f"用户输入: '{text}'")
    print(f"提取实体: {json.dumps(entities, ensure_ascii=False, indent=2)}")
