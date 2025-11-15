import os
from typing import Dict, List, Optional

from dsl.dsl_parser import DslParser, ChatFlow
from dsl.interpreter import Interpreter
from core.action_executor import ActionExecutor
from core.session_manager import SessionManager, Session

class Chatbot:
    """
    The main orchestrator for the chatbot. It loads all flows, manages sessions,
    and routes user input to the appropriate interpreter.
    """
    def __init__(self, flows_dir: str = "dsl/flows"):
        self.flows: Dict[str, ChatFlow] = self._load_flows(flows_dir)
        self.interpreters: Dict[str, Interpreter] = {
            name: Interpreter(flow) for name, flow in self.flows.items()
        }
        self.session_manager = SessionManager()
        self.action_executor = ActionExecutor()
        print(f"Chatbot initialized with {len(self.flows)} flows.")

    def _load_flows(self, flows_dir: str) -> Dict[str, ChatFlow]:
        """Loads all DSL flow files from a directory."""
        flows = {}
        if not os.path.exists(flows_dir):
            print(f"Warning: Flows directory not found at '{flows_dir}'")
            return flows
            
        for root, _, files in os.walk(flows_dir):
            for filename in files:
                if filename.endswith(".yaml"):
                    file_path = os.path.join(root, filename)
                    parser = DslParser(file_path)
                    flow = parser.get_flow()
                    if flow:
                        flows[flow.name] = flow
                        print(f"  - Loaded flow: '{flow.name}' from {filename}")
        return flows

    def handle_message(self, session_id: str, user_input: str) -> List[str]:
        """
        Handles a user's message, routes it to the correct flow, and returns the bot's responses.
        """
        session = self.session_manager.get_session(session_id)
        session.last_user_input = user_input
        
        active_flow_name = session.get("active_flow_name")
        interpreter = self.interpreters.get(active_flow_name) if active_flow_name else None

        # If already in a flow, continue with it
        if interpreter:
            actions = interpreter.process(session, user_input)
            # A simple way to end a flow: if the next state is an end state with no actions.
            next_state = self.flows[active_flow_name].get_state(session.current_state_id)
            if "end" in session.current_state_id and not next_state.get("actions"):
                session.set("active_flow_name", None) # End of flow
        else:
            # If not in a flow, try to find a trigger in all flows
            actions = []
            for flow_name, flow in self.flows.items():
                entry_state = flow.get_entry_state()
                if entry_state:
                    for trigger in entry_state.get("triggers", []):
                        if trigger.get("type") == "regex":
                            if re.search(trigger.get("value", ""), user_input):
                                print(f"[Chatbot] Triggered flow '{flow_name}'")
                                session.set("active_flow_name", flow_name)
                                interpreter = self.interpreters[flow_name]
                                # Get the initial actions of the new flow
                                actions = interpreter.get_initial_actions()
                                session.current_state_id = flow.entry_point
                                break
                if interpreter:
                    break
        
        if not actions and not interpreter:
            return ["抱歉，我暂时无法理解您的意思。"]
            
        # Execute actions
        responses = self.action_executor.execute(actions, session.to_dict())
        return responses

# A simple regex import needed for trigger matching
import re
