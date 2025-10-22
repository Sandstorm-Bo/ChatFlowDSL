import yaml
from typing import List, Dict, Any, Optional

class ChatFlow:
    """A class to hold the parsed chat flow data and provide easy access."""
    def __init__(self, data: Dict[str, Any]):
        self._data = data
        self.name: str = data.get("name", "Untitled Flow")
        self.entry_point: str = data.get("entry_point")
        self.states: List[Dict[str, Any]] = data.get("states", [])
        self._states_by_id: Dict[str, Dict[str, Any]] = {state['id']: state for state in self.states if 'id' in state}

    def get_state(self, state_id: str) -> Optional[Dict[str, Any]]:
        """Get a state by its ID."""
        return self._states_by_id.get(state_id)

    def get_entry_state(self) -> Optional[Dict[str, Any]]:
        """Get the entry point state of the flow."""
        if not self.entry_point:
            return None
        return self.get_state(self.entry_point)

    def __repr__(self) -> str:
        return f"<ChatFlow name='{self.name}' entry='{self.entry_point}' state_count={len(self.states)}>"


class DslParser:
    """Parses a DSL file, validates its basic structure, and loads it into a ChatFlow object."""
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.flow_data = self._load_and_validate()

    def _load_and_validate(self) -> Optional[Dict[str, Any]]:
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Error: DSL file not found at {self.file_path}")
            return None
        except yaml.YAMLError as e:
            print(f"Error parsing DSL file: {e}")
            return None

        if not isinstance(data, dict):
            print("Error: DSL root should be a dictionary.")
            return None

        # Basic validation
        if "name" not in data or "states" not in data or "entry_point" not in data:
            print("Error: DSL must contain 'name', 'states', and 'entry_point' fields.")
            return None
            
        if not isinstance(data["states"], list):
            print("Error: 'states' must be a list.")
            return None

        return data

    def get_flow(self) -> Optional[ChatFlow]:
        """Returns the parsed chat flow as a ChatFlow object."""
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
