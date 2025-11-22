import yaml
from typing import List, Dict, Any, Optional

class ChatFlow:
    """存储解析后的流程数据"""
    def __init__(self, data: Dict[str, Any]):
        self._data = data
        self.name: str = data.get("name", "Untitled Flow")
        self.entry_point: str = data.get("entry_point")
        self.states: List[Dict[str, Any]] = data.get("states", [])
        self._states_by_id: Dict[str, Dict[str, Any]] = {state['id']: state for state in self.states if 'id' in state}

    def get_state(self, state_id: str) -> Optional[Dict[str, Any]]:
        """根据状态ID获取状态"""
        return self._states_by_id.get(state_id)

    def get_entry_state(self) -> Optional[Dict[str, Any]]:
        """获取流程入口状态"""
        if not self.entry_point:
            return None
        return self.get_state(self.entry_point)

    def __repr__(self) -> str:
        return f"<ChatFlow name='{self.name}' entry='{self.entry_point}' state_count={len(self.states)}>"


class DslParser:
    """DSL文件解析器，将YAML流程定义转换为ChatFlow对象"""
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.flow_data = self._load_and_validate()

    def _load_and_validate(self) -> Optional[Dict[str, Any]]:
        """加载并验证DSL文件"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except FileNotFoundError:
            print(f"错误：DSL文件不存在 {self.file_path}")
            return None
        except yaml.YAMLError as e:
            print(f"错误：DSL文件解析失败 {e}")
            return None

        if not isinstance(data, dict):
            print("错误：DSL根节点必须是字典")
            return None

        if "name" not in data or "states" not in data or "entry_point" not in data:
            print("错误：DSL必须包含 'name', 'states', 'entry_point' 字段")
            return None

        if not isinstance(data["states"], list):
            print("错误：'states' 必须是列表")
            return None

        return data

    def get_flow(self) -> Optional[ChatFlow]:
        """返回解析后的流程对象"""
        if self.flow_data:
            return ChatFlow(self.flow_data)
        return None

if __name__ == '__main__':
    # 示例用法
    parser = DslParser('dsl/examples/refund_flow.v2.yaml')
    chat_flow = parser.get_flow()

    if chat_flow:
        print(f"Successfully loaded flow: {chat_flow}")
        
        entry_state = chat_flow.get_entry_state()
        if entry_state:
            print(f"Entry point '{chat_flow.entry_point}' found.")
            # print("Entry state data:", entry_state)
        else:
            print(f"Error: Entry point '{chat_flow.entry_point}' not found in states.")

        # Test getting another state
        test_state = chat_flow.get_state("state_collect_reason")
        if test_state:
            print("Successfully retrieved state 'state_collect_reason'.")
        else:
            print("Failed to retrieve state 'state_collect_reason'.")
    else:
        print("Failed to load or validate DSL file.")
