import yaml
from typing import List, Dict, Any

## 脚本文件解析器
class DslParser:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.rules = self._load_rules()

    def _load_rules(self) -> List[Dict[str, Any]]:
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Error: DSL file not found at {self.file_path}")
            return []
        except yaml.YAMLError as e:
            print(f"Error parsing DSL file: {e}")
            return []

    def get_rules(self) -> List[Dict[str, Any]]:
        return self.rules

if __name__ == '__main__':
    # 示例用法
    parser = DslParser('dsl/examples/refund_zh.yaml')
    rules = parser.get_rules()
    import json
    print(json.dumps(rules, indent=2, ensure_ascii=False))
