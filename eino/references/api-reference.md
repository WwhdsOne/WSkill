# Eino API Reference

Detailed API documentation organized by layer. Use this as a lookup reference
when you need exact function signatures, option types, or configuration details.

## Table of Contents

- [Schema Layer](#schema-layer)
- [Components Layer](#components-layer)
- [Compose Layer](#compose-layer)
- [ADK Layer](#adk-layer)
- [Callbacks Layer](#callbacks-layer)

---

## Schema Layer

Package: `github.com/cloudwego/eino/schema`

### Message

The universal unit of communication between the application and LLM.

```go
type Message struct {
    Role         RoleType      // System, User, Assistant, Tool
    Content      string        // Text content
    MultiContent []ChatMessagePart // Multimodal content (images, etc.)
    ToolCalls    []ToolCall    // Tool calls from assistant
    ToolCallID   string        // ID for tool response messages
    ToolName     string        // Tool name for tool messages
    ResponseMeta *ResponseMeta // Token usage, finish reason, etc.
    Extra        map[string]any // Provider-specific data
}
```

**Constructors:**
```go
schema.SystemMessage(content string) *Message
schema.UserMessage(content string) *Message
schema.AssistantMessage(content string, toolCalls []ToolCall) *Message
schema.ToolMessage(content string, toolCallID string) *Message
```

**Role constants:** `schema.System`, `schema.User`, `schema.Assistant`, `schema.Tool`

**ToolCall:**
```go
type ToolCall struct {
    ID       string
    Type     string
    Function FunctionCall
}

type FunctionCall struct {
    Name      string
    Arguments string // JSON string
}
```

### ToolInfo

Describes a tool for the model's function calling.

```go
type ToolInfo struct {
    Name        string
    Description string
    ParamsOneOf *ParamsOneOf // JSON Schema 2020-12 parameter definition
}

type ParamsOneOf struct {
    Params map[string]*ParameterInfo
}

type ParameterInfo struct {
    Type     string           // "string", "number", "boolean", "object", "array"
    Desc     string
    Required bool
    Enum     []string
    SubParams map[string]*ParameterInfo // For nested objects
    ItemParams *ParameterInfo          // For array items
}
```

### Document

Text chunk with metadata for retrieval-augmented generation.

```go
type Document struct {
    ID          string
    Content     string
    MetaData    map[string]any
    Score       float64 // Relevance score from retriever
    DenseVector []float64
    SparseVector map[int]float64
}
```

### StreamReader / StreamWriter

Read-once streaming data types (single goroutine consumer).

```go
type StreamReader[T any] struct { ... }

func (sr *StreamReader[T]) Recv() (T, error)  // Receive next chunk
func (sr *StreamReader[T]) Close()             // Close the stream

type StreamWriter[T any] struct { ... }

func (sw *StreamWriter[T]) Send(chunk T, err error) // Send a chunk or error
func (sw *StreamWriter[T]) Close()                   // Close the stream

// Create a pipe pair
func Pipe[T any](capacity int) (*StreamReader[T], *StreamWriter[T])
```

### ToolChoice

Controls how the model uses tools.

```go
type ToolChoice int

const (
    ToolChoiceForbidden ToolChoice = iota // Model must NOT use tools
    ToolChoiceAllowed                     // Model MAY use tools (default)
    ToolChoiceForced                      // Model MUST use a tool
)
```

### Message Template Placeholders

```go
func MessagesPlaceholder(key string, optional bool) *Message
```

---

## Components Layer

Package: `github.com/cloudwego/eino/components/*`

### ChatModel (`components/model`)

```go
// BaseChatModel — basic chat model
type BaseChatModel interface {
    Generate(ctx context.Context, input []*schema.Message, opts ...Option) (*schema.Message, error)
    Stream(ctx context.Context, input []*schema.Message, opts ...Option) (*schema.StreamReader[*schema.Message], error)
}

// ToolCallingChatModel — model with tool binding
type ToolCallingChatModel interface {
    BaseChatModel
    WithTools(tools []*schema.ToolInfo) (ToolCallingChatModel, error)
}

// AgenticChatModel — model that returns AgenticMessage (includes action events)
type AgenticChatModel interface {
    BaseChatModel
}

// AgenticMessage — wraps a Message with optional action events
type AgenticMessage = TypedAgenticMessage[*schema.Message]
```

### Tool (`components/tool`)

```go
// BaseTool — basic tool info
type BaseTool interface {
    Info(ctx context.Context) (*schema.ToolInfo, error)
}

// InvokableTool — sync tool execution
type InvokableTool interface {
    BaseTool
    InvokableRun(ctx context.Context, argumentsInJSON string, opts ...Option) (string, error)
}

// StreamableTool — streaming tool execution
type StreamableTool interface {
    BaseTool
    StreamableRun(ctx context.Context, argumentsInJSON string, opts ...Option) (*schema.StreamReader[string], error)
}
```

### Retriever (`components/retriever`)

```go
type Retriever interface {
    Retrieve(ctx context.Context, query string, opts ...Option) ([]*schema.Document, error)
}
```

### Embedder (`components/embedding`)

```go
type Embedder interface {
    EmbedStrings(ctx context.Context, texts []string, opts ...Option) ([][]float64, error)
}
```

### Indexer (`components/indexer`)

```go
type Indexer interface {
    Store(ctx context.Context, docs []*schema.Document, opts ...Option) error
}
```

### Prompt (`components/prompt`)

```go
// ChatTemplate — format messages from variables
type ChatTemplate interface {
    Format(ctx context.Context, vs map[string]any) ([]*schema.Message, error)
}

// Create from f-string messages
func FromMessages(formatType FormatType, msgs ...*schema.Message) (ChatTemplate, error)
```

### Document (`components/document`)

```go
// Loader — load documents from a source
type Loader interface {
    Load(ctx context.Context, opts ...Option) ([]*schema.Document, error)
}

// Transformer — split/transform documents
type Transformer interface {
    Transform(ctx context.Context, docs []*schema.Document, opts ...Option) ([]*schema.Document, error)
}
```

---

## Compose Layer

Package: `github.com/cloudwego/eino/compose`

### Graph

DAG-based orchestration engine.

```go
// Create a new graph
func NewGraph[I, O any](opts ...NewGraphOption) *Graph[I, O]

// Add nodes
func (g *Graph[I, O]) AddChatModelNode(key string, model model.BaseChatModel) error
func (g *Graph[I, O]) AddToolsNode(key string, config *ToolsNodeConfig) error
func (g *Graph[I, O]) AddRetrieverNode(key string, retriever retriever.Retriever) error
func (g *Graph[I, O]) AddChatTemplateNode(key string, template prompt.ChatTemplate) error
func (g *Graph[I, O]) AddLambdaNode(key string, lambda *Lambda) error
func (g *Graph[I, O]) AddEmbeddingNode(key string, embedder embedding.Embedder) error
func (g *Graph[I, O]) AddIndexerNode(key string, indexer indexer.Indexer) error
func (g *Graph[I, O]) AddDocumentTransformerNode(key string, t document.Transformer) error
func (g *Graph[I, O]) AddBranchNode(key string, branch *GraphBranch) error
func (g *Graph[I, O]) AddPassthroughNode(key string) error
func (g *Graph[I, O]) AddGraphNode(key string, graph *Graph[any, any]) error

// Add edges
func (g *Graph[I, O]) AddEdge(from, to string) error

// Add conditional branching
func (g *Graph[I, O]) AddBranch(nodeKey string, branch *GraphBranch) error

// Compile to a runnable
func (g *Graph[I, O]) Compile(ctx context.Context, opts ...CompileOption) (Runnable[I, O], error)

// Branch condition
func NewGraphBranch[T any](
    condition func(context.Context, T) (string, error),
    ends map[string]bool,
) *GraphBranch
```

**Special node keys:**
- `compose.START` — graph entry point
- `compose.END` — graph exit point

### Chain

Linear pipeline builder.

```go
func NewChain[I, O any](opts ...NewGraphOption) *Chain[I, O]

func (c *Chain[I, O]) AppendChatModel(model interface{}) error
func (c *Chain[I, O]) AppendChatTemplate(template interface{}) error
func (c *Chain[I, O]) AppendToolsNode(config *ToolsNodeConfig) error
func (c *Chain[I, O]) AppendRetriever(retriever interface{}) error
func (c *Chain[I, O]) AppendLambda(lambda *Lambda) error
func (c *Chain[I, O]) AppendGraph(graph *Graph[any, any]) error
func (c *Chain[I, O]) AppendParallel() error
func (c *Chain[I, O]) AppendBranch(branch *ChainBranch) error
func (c *Chain[I, O]) AppendPassthrough() error
func (c *Chain[I, O]) Compile(ctx context.Context, opts ...CompileOption) (Runnable[I, O], error)
```

To use a Graph as a sub-graph within a Chain, compile it first to a Runnable, then wrap it as a Lambda with `compose.InvokableLambda` or `compose.StreamableLambda`.

### Runnable

The result of compiling a Graph or Chain.

```go
type Runnable[I, O any] interface {
    // Sync input → sync output
    Invoke(ctx context.Context, input I, opts ...Option) (O, error)

    // Sync input → stream output
    Stream(ctx context.Context, input I, opts ...Option) (*schema.StreamReader[O], error)

    // Stream input → sync output
    Collect(ctx context.Context, input *schema.StreamReader[I], opts ...Option) (O, error)

    // Stream input → stream output
    Transform(ctx context.Context, input *schema.StreamReader[I], opts ...Option) (*schema.StreamReader[O], error)
}
```

### Lambda

Wrap a Go function as a graph node.

```go
// Create a sync lambda
func InvokableLambda[I, O any](fn func(context.Context, I) (O, error)) *Lambda

// Create a streaming lambda
func StreamableLambda[I, O any](fn func(context.Context, I) (*schema.StreamReader[O], error)) *Lambda
```

### Branch

```go
// Graph branch (used with Graph.AddBranch)
func NewGraphBranch[T any](
    condition func(context.Context, T) (string, error),
    ends map[string]bool,
) *GraphBranch

// Chain branch (used with Chain.AppendBranch)
func NewChainBranch[T any](
    condition func(context.Context, T) (string, error),
    ends map[string]bool,
) *ChainBranch
```

### Parallel

```go
func NewParallel() *Parallel

func (p *Parallel) Add(key string, node interface{}) error
```

### ToolsNodeConfig

```go
type ToolsNodeConfig struct {
    Tools              []tool.BaseTool
    ToolCallMiddlewares []ToolMiddleware
}

type ToolMiddleware struct {
    Invokable          func(ctx context.Context, tool tool.InvokableTool, next tool.InvokableTool) tool.InvokableTool
    Streamable         func(ctx context.Context, tool tool.StreamableTool, next tool.StreamableTool) tool.StreamableTool
    EnhancedInvokable  func(ctx context.Context, tool tool.InvokableTool, next tool.InvokableTool) tool.InvokableTool
    EnhancedStreamable func(ctx context.Context, tool tool.StreamableTool, next tool.StreamableTool) tool.StreamableTool
}
```

### Graph Tool

Wrap a compiled Graph as a tool for agents.

```go
// NewInvokableGraphTool wraps a graph as an invokable tool
func graphtool.NewInvokableGraphTool(graph interface{}, name, description string) (tool.InvokableTool, error)

// NewStreamableGraphTool wraps a graph as a streamable tool
func graphtool.NewStreamableGraphTool(graph interface{}, name, description string) (tool.StreamableTool, error)
```

---

## ADK Layer

Package: `github.com/cloudwego/eino/adk`

### Agent Interface

```go
type Agent interface {
    Name(ctx context.Context) string
    Description(ctx context.Context) string
    Run(ctx context.Context, input *AgentInput, opts ...AgentRunOption) *AsyncIterator[*AgentEvent]
}

type ResumableAgent interface {
    Agent
    Resume(ctx context.Context, info *ResumeInfo, opts ...AgentRunOption) *AsyncIterator[*AgentEvent]
}
```

### AgentInput / AgentEvent

```go
type AgentInput struct {
    Messages []Message // []*schema.Message
    EnableStreaming bool
    // Session data, etc.
}

type AgentEvent struct {
    AgentName string

    // Output message (streaming delta or full message)
    Message *MessageOutput

    // Action events: interrupt, exit, transfer, break loop
    Action *AgentAction
}

func (e *AgentEvent) Message() (*MessageOutput, bool) // Returns message if present

type MessageOutput struct {
    Role    schema.RoleType
    Content string        // Delta in streaming mode, full text otherwise
    IsDelta bool          // True during streaming
}

type AgentAction struct {
    Exit          *ExitAction
    Interrupted   *InterruptAction
    TransferToAgent *TransferToAgentAction
    BreakLoop     *BreakLoopAction
}
```

### ChatModelAgent

```go
type ChatModelAgent = TypedChatModelAgent[*schema.Message]

// TypedChatModelAgentConfig is ChatModelAgentConfig for *schema.Message type.
type ChatModelAgentConfig = TypedChatModelAgentConfig[*schema.Message]

// Create a chat model agent
func NewChatModelAgent(ctx context.Context, config *ChatModelAgentConfig) (*ChatModelAgent, error)
```

**ChatModelAgentConfig fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `Name` | `string` | Required for sub-agents | Agent name (unique recommended) |
| `Description` | `string` | Required for sub-agents | What this agent can do |
| `Instruction` | `string` | No | System prompt (supports f-string with session values) |
| `Model` | `model.BaseModel[*schema.Message]` | **Yes** | The chat model |
| `ToolsConfig` | `adk.ToolsConfig` | No | Tool configuration |
| `GenModelInput` | `adk.GenModelInput` | No | Custom model input formatter |
| `MaxIterations` | `int` | No | Max ReAct loop iterations (default: 20) |
| `Exit` | `tool.BaseTool` | No | Exit tool for agent termination |
| `OutputKey` | `string` | No | Store output in session under this key |
| `Middlewares` | `[]AgentMiddleware` | No | Deprecated — use Handlers |
| `Handlers` | `[]ChatModelAgentMiddleware` | No | Interface-based middleware handlers |

### Runner

```go
type Runner struct{ ... }

type RunnerConfig struct {
    Agent           Agent
    EnableCheckPoint bool  // Enable checkpoint persistence
    // ... additional config
}

func NewRunner(ctx context.Context, conf RunnerConfig) *Runner

// Run starts agent execution and returns an event iterator.
func (r *Runner) Run(ctx context.Context, messages []*schema.Message, opts ...AgentRunOption) *AsyncIterator[*AgentEvent]

// Resume continues execution from a checkpoint.
func (r *Runner) Resume(ctx context.Context, checkpointID string, resumeData map[string]any, opts ...AgentRunOption) *AsyncIterator[*AgentEvent]

// CheckPointID returns the current checkpoint ID.
func (r *Runner) CheckPointID() string
```

### Session Values

Share data across agent runs via context.

```go
func AddSessionValue(ctx context.Context, key string, value any) context.Context
func GetSessionValue(ctx context.Context, key string) (any, bool)
func GetSessionValues(ctx context.Context) map[string]any
```

### Interrupt / Resume

```go
// Pause agent execution and wait for human input.
func InterruptAndWait(ctx context.Context, data map[string]any) error

// Get data provided during resume.
func GetResumeData(ctx context.Context) map[string]any
```

### Agent Tool

Wrap an agent as a tool for another agent.

```go
func NewAgentTool(ctx context.Context, agent Agent, opts ...AgentToolOption) (tool.BaseTool, error)

func WithAgentToolDescription(desc string) AgentToolOption
func WithAgentToolName(name string) AgentToolOption
```

### Transfer Between Agents

```go
// Standard transfer tool names (used internally by DeepAgent, etc.)
const (
    TransferToAgentToolName = "transfer_to_agent"
)

// Transfer action in AgentEvent
type TransferToAgentAction struct {
    TargetAgentName string
    Message         string
}
```

### AsyncIterator

Returned by Agent.Run() and Runner.Run().

```go
type AsyncIterator[T any] struct { ... }

func (it *AsyncIterator[T]) Next() bool  // Advance to next event
func (it *AsyncIterator[T]) Value() T   // Get current event
```

### Prebuilt Agents

#### DeepAgent

Multi-agent orchestration that automatically creates tools for sub-agents.

```go
// github.com/cloudwego/eino/adk/prebuilt/deep
func New(ctx context.Context, cfg *Config) (adk.ResumableAgent, error)

type Config struct {
    Name              string
    Model             model.ToolCallingChatModel  // or model.BaseChatModel
    SubAgents         []adk.Agent
    // ... additional config
}
```

#### PlanExecuteAgent

Plan-then-execute pattern: planner creates a plan, executor carries it out.

```go
// github.com/cloudwego/eino/adk/prebuilt/planexecute
func New(ctx context.Context, cfg *Config) (adk.ResumableAgent, error)

type Config struct {
    Name        string
    Description string
    Planner     model.ToolCallingChatModel  // Model that creates plans
    Executor    model.ToolCallingChatModel  // Model that executes plans
    Tools       []tool.BaseTool
    // ... additional config
}
```

### Middleware Ecosystem

Located under `github.com/cloudwego/eino/adk/middlewares/`:

| Package | Purpose |
|---------|---------|
| `filesystem` | File system operations for agents |
| `skill` | Tool execution skills |
| `summarization` | Auto-summarize conversation history |
| `plantask` | Plan and task tracking |
| `toolsearch` | Dynamic tool discovery |
| `reduction` | Tool result reduction |
| `patchtoolcalls` | Patch/modify tool calls mid-execution |
| `dynamictool` | Register tools dynamically at runtime |
| `agentsmd` | Agent SMD (Service Metadata) |

---

## Callbacks Layer

Package: `github.com/cloudwego/eino/callbacks`

### Handler Builder

```go
handler := callbacks.NewHandlerBuilder().
    OnStartFn(func(ctx context.Context, info *RunInfo, input CallbackInput) context.Context {
        // Called when a component starts. Return modified ctx to pass data to OnEnd.
        return ctx
    }).
    OnEndFn(func(ctx context.Context, info *RunInfo, output CallbackOutput) context.Context {
        // Called when a component finishes.
        return ctx
    }).
    OnErrorFn(func(ctx context.Context, info *RunInfo, err error) context.Context {
        // Called when a component errors.
        return ctx
    }).
    OnStartWithStreamInputFn(func(ctx context.Context, info *RunInfo, input *schema.StreamReader[CallbackInput]) context.Context {
        // Called when streaming input starts.
        return ctx
    }).
    OnEndWithStreamOutputFn(func(ctx context.Context, info *RunInfo, output *schema.StreamReader[CallbackOutput]) context.Context {
        // Called when streaming output ends.
        return ctx
    }).
    Build()
```

### RunInfo

```go
type RunInfo struct {
    Name      string // Node/component name
    Type      string // Component type (e.g., "ChatModel", "Tool", "Lambda")
    Component Component // The component type enum
}
```

### Registration

```go
// Register globally (call once at startup; NOT thread-safe after)
callbacks.AppendGlobalHandlers(handler)

// Attach per-invocation
runnable.Invoke(ctx, input, compose.WithCallbacks(handler))

// Target a specific node
compose.WithCallbacks(handler).DesignateNode("myModelName")
```
