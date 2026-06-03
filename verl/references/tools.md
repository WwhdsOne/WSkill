# Tools, Agent Loops & Multi-Turn Interactions

verl supports training models for tool use and multi-turn interactions through two main components: the **Tool Framework** and the **Agent Loop**.

## Tool Framework (`verl/tools/`)

The tool framework enables models to call external functions during generation — for code execution, web search, calculator use, etc.

### Architecture

```
verl/tools/
├── base_tool.py         # Base class for all tools
├── function_tool.py     # Function-based tool wrapper
├── schemas.py           # OpenAI-compatible tool schemas
└── tool_registry.py     # Tool registration
```

### Base Tool Class (`verl/tools/base_tool.py`)

All tools inherit from `BaseTool`:

```python
class BaseTool:
    """Base class for all tools in verl."""
    
    def __init__(self, config: dict):
        self.config = config
    
    def get_openai_tool_schema(self) -> dict:
        """Return OpenAI-compatible tool schema."""
        raise NotImplementedError
    
    def execute(self, **kwargs) -> tuple[str, float]:
        """Execute the tool and return (result, reward)."""
        raise NotImplementedError
```

### Pre-built Tools

verl ships with several built-in tools:

| Tool | Description |
|------|-------------|
| `PythonExecTool` | Execute Python code in sandbox |
| `CalculatorTool` | Mathematical calculations |
| `WebSearchTool` | Web search integration |
| `FileIOTool` | File read/write operations |

### Creating a Custom Tool

```python
# my_custom_tool.py
from verl.tools.base_tool import BaseTool

class MyCustomTool(BaseTool):
    def get_openai_tool_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": "my_tool",
                "description": "Description of what this tool does",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "param1": {
                            "type": "string",
                            "description": "Description of param1"
                        }
                    },
                    "required": ["param1"]
                }
            }
        }
    
    def execute(self, param1: str, **kwargs) -> tuple[str, float]:
        result = f"Processed: {param1}"
        reward = 0.0
        return result, reward
```

### Registering Tools

Tools are registered via the Hydra config system:

```yaml
# In your config
tools:
  - name: my_custom_tool
    module: my_custom_tool
    class: MyCustomTool
    config:
      option1: value1
  - name: python_exec
    module: verl.tools.python_exec
    class: PythonExecTool
    config:
      timeout: 30
      max_memory: "1GB"
```

## Agent Loop (`verl/experimental/agent_loop/`)

The Agent Loop manages the interaction cycle between the model and tools, enabling multi-turn dialogue where the model can call tools and receive results.

### Architecture

```
verl/experimental/agent_loop/
├── agent_loop.py              # AgentLoopManager (orchestration)
├── single_turn_agent_loop.py  # Standard single-turn rollout
├── tool_agent_loop.py         # Multi-turn with tool calling
└── tool_parser.py             # Parse tool calls from model output
```

### Agent Loop Types

#### SingleTurnAgentLoop
- Standard rollout: prompt → response
- No tool calling, no multi-turn
- Used for standard PPO/GRPO training

#### ToolAgentLoop
- Multi-turn: prompt → response → tool call → tool result → response → ...
- Model can call tools multiple times in a single trajectory
- Manages tool execution and result formatting
- Supports max_turns limit to prevent infinite loops

### Tool Agent Loop Flow

```
┌─────────────┐
│   Prompt     │
└──────┬──────┘
       ▼
┌─────────────┐     ┌──────────────┐
│ Model Gen   │────►│ Parse Output  │
│ (generate   │     │ (tool_parser) │
│  response)  │◄────┤               │
└──────┬──────┘     └──────┬───────┘
       │                   │
       │     ┌─────────────┘
       ▼     ▼
  ┌──────────────┐     ┌──────────────┐
  │ Text Only?   │     │ Tool Call?   │
  │ → Return     │     │ → Execute    │
  └──────────────┘     └──────┬───────┘
                               │
                         ┌─────▼──────┐
                         │ Execute    │
                         │ Tool       │
                         └─────┬──────┘
                               │
                         ┌─────▼──────┐
                         │ Format     │
                         │ Result as  │
                         │ Message    │
                         └─────┬──────┘
                               │
                     ┌─────────▼──────┐
                     │ Append to      │
                     │ conversation   │
                     │ → Generate again│
                     └────────────────┘
```

### Configuring Agent Loop

```yaml
# agent_loop config
agent_loop:
  type: tool_agent_loop       # or single_turn_agent_loop
  max_turns: 5                # Max tool-calling turns
  max_tokens_per_turn: 1024   # Max tokens generated per turn
  stop_on_no_tool_call: true   # Stop when model stops calling tools
  
  # Tool config
  tools: [...]                # List of available tools
  
  # System prompt
  system_prompt: "You are a helpful assistant with access to tools..."

# Enable agent loop
actor_rollout_ref.rollout.agent.enable_agent_loop: true
```

### Tool Parser (`verl/experimental/agent_loop/tool_parser.py`)

Parses model outputs to extract tool calls. Supports multiple formats:

| Format | Example | Parser |
|--------|---------|--------|
| OpenAI function call | `{"name": "calc", "arguments": {...}}` | `openai_tool_parser` |
| XML tags | `<tool_call>calc(1+1)</tool_call>` | `xml_tool_parser` |
| Custom regex | User-defined format | Custom parser |

### AgentLoopManager

Coordinates multiple agent loops running in parallel across Ray workers:

- Manages tool execution lifecycle
- Handles batching of tool executions
- Collects trajectories for training
- Manages conversation state between turns

```python
from verl.experimental.agent_loop import AgentLoopManager

manager = AgentLoopManager(config)
trajectories = manager.run_agent_loops(prompts)
# trajectories contain multi-turn conversation history
# with tool calls and results interleaved
```

## Reward Loops (`verl/experimental/reward_loop/`)

Async reward computation that can run independently from the training loop:

- **Purpose**: Decouple reward computation from training for complex reward functions
- **Use case**: Reward models that need separate GPU, long-running computation (code execution), or external API calls

## Teacher Loops (`verl/experimental/teacher_loop/`)

Multi-teacher model loop for knowledge distillation:

- Multiple teacher models can provide different signals
- Used in knowledge distillation scenarios
- Coordinates multiple teacher queries per training step

## Async Policy Training (`verl/experimental/fully_async_policy/`)

Fully asynchronous policy training where actors don't wait for rollouts:

- **Fully async**: Complete decoupling of rollout and training
- **One-step off-policy**: Uses slightly stale rollouts for one gradient step

## Best Practices for Tool-Calling Training

1. **Start simple**: Begin with 1-2 tools, add more as training stabilizes
2. **Use clear tool descriptions**: Models learn better with well-documented tool schemas
3. **Limit max turns**: Prevent infinite loops with `max_turns`
4. **Include tool use examples in prompts**: Few-shot examples help models learn tool calling
5. **Monitor tool call success rate**: Track how often tool calls succeed vs fail
6. **Penalize failed tool calls**: Set `tool_call_reward` to negative for failures
7. **Use SGLang for tool calling**: SGLang's structured generation is better for tool call parsing
