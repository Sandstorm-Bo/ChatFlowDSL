from typing import List, Dict, Any

class ActionExecutor:
    def execute(self, actions: List[Dict[str, Any]], session: Dict[str, Any]) -> List[str]:
        """
        Executes a list of actions and returns a list of text responses for the user.
        """
        responses = []
        for action in actions:
            action_type = action.get("type")
            
            if action_type == "respond":
                response_text = self._handle_respond(action, session)
                if response_text:
                    responses.append(response_text)
            elif action_type == "extract_variable":
                self._handle_extract_variable(action, session)
            elif action_type == "set_variable":
                self._handle_set_variable(action, session)
            # 'wait_for_input' is a passive action, handled by the interpreter's logic flow.
            # No operation needed here.
            elif action_type == "wait_for_input":
                pass
            else:
                print(f"Warning: Unknown action type '{action_type}'")
        
        return responses

    def _handle_respond(self, action: Dict[str, Any], session: Dict[str, Any]) -> str:
        """Handles the 'respond' action."""
        text = action.get("text", "")
        # A simple template engine for variables like {{session.order_id}}
        # For a real application, consider using libraries like Jinja2.
        import re
        def repl(match):
            parts = match.group(1).split('.')
            if len(parts) == 2 and parts[0] == 'session':
                return str(session.get("variables", {}).get(parts[1], ''))
            return ''
        
        # Replace {{session.variable_name}}
        processed_text = re.sub(r"\{\{\s*session\.(\w+)\s*\}\}", repl, text)
        return processed_text

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
