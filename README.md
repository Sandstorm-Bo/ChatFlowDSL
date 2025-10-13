# ChatFlowDSL

This project is a Domain-Specific Language (DSL) and interpreter for creating intelligent chatbot workflows. It allows defining conversation logic using a simple YAML-based syntax and integrates with Large Language Models (LLMs) for natural language understanding.

## Features (Minimal Framework)

- **DSL Parser**: Loads conversation rules from `.yaml` files.
- **Interpreter**: Processes user input based on parsed rules.
- **LLM Integration (Mock)**: Simulates intent recognition.
- **Command-Line Interface**: A simple, interactive CLI for chatting.

## Project Structure

```
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── config/
│   └── config.yaml         # Configuration file
├── dsl/
│   ├── dsl_parser.py       # Parses the DSL files
│   ├── interpreter.py      # Executes DSL logic
│   └── examples/
│       └── refund_zh.yaml  # Example DSL script
├── llm/
│   └── llm_responder.py    # Handles LLM communication
├── core/                   # Core business logic (for advanced features)
│   └── ...
├── cli/
│   └── cli_interface.py    # Command-line interface
└── tests/
    └── test_interpreter.py # Tests for the interpreter
```

## How to Run

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure API Key:**
    Open `config/config.yaml` and replace `"YOUR_OPENAI_API_KEY"` with your actual LLM API key.

3.  **Run the application:**
    ```bash
    python main.py
    ```
