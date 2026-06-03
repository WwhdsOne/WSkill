---
name: eino
description: >
  Build AI agents, chatbots, and LLM applications in Go using the Eino framework by ByteDance/CloudWeGo.
  Use this skill for ANY Go-based AI/LLM work — building a chatbot, adding tool/function calling,
  creating RAG pipelines (retrieval-augmented generation), building multi-agent systems, wiring LLM
  workflows with graphs, adding streaming/observability, or implementing human-in-the-loop patterns.
  Triggers on mentions of "eino", "ChatModelAgent", "ChatModel", "ADK", "Go agent", "Go chatbot",
  "Go AI", "Go LLM", "Go RAG", "Go tool calling", "Go 智能体", "Go 聊天机器人", or any request to
  build an LLM-powered feature in Go. Covers eino core (schema, components, compose/graph, ADK agents,
  callbacks) and eino-ext (OpenAI, Ollama, Redis, Milvus implementations).
---

# Eino Skill

Eino is ByteDance's Go framework for building LLM applications. This skill provides guidance
and code generation for the entire Eino ecosystem — from low-level schema types through
component abstractions, graph-based orchestration, to the Agent Development Kit (ADK).

## When to Use This Skill

Use this skill whenever the user needs to:

1. **Build an AI agent** — ChatModelAgent, DeepAgent, PlanExecuteAgent, or custom agent
2. **Build a chatbot or conversational AI** — using eino's ADK with Runner
3. **Build a RAG pipeline** — using retriever + chat model in a compose graph
4. **Add tool calling** — define tools and wire them to a chat model
5. **Build multi-agent systems** — DeepAgent orchestration, agent-to-agent transfer
6. **Add observability** — callbacks for logging, tracing, metrics
7. **Wire components together** — using Compose (Graph, Chain, Branch, Parallel)
8. **Generate any Go code involving LLM/agent patterns** — even if the user doesn't mention eino
   explicitly, if they're describing an LLM application in Go, this is the skill to use

Also use this skill when the user asks questions about eino concepts (schema, components,
compose, ADK, callbacks) or about eino-ext component implementations (OpenAI, Ollama,
Redis, etc.).

## Reference Files

The skill is organized for progressive disclosure. Read files as needed:

- **`references/recipes.md`** — Common usage recipes with complete, runnable code examples.
  Start here when the user wants working code for a specific pattern.
- **`references/api-reference.md`** — Detailed API documentation covering all layers.
  Read this when you need exact function signatures, option types, or configuration details.
- **`references/eino-ext.md`** — Component implementations from eino-ext (OpenAI, Ollama,
  Redis retriever, etc.). Read when the user needs specific model/component implementations.

## Quick Reference: Framework Layers

Eino is organized in four layers, from low-level to high-level:

```
ADK (Agent Development Kit)          ← Agent runtime, Runner, middleware
  │  ChatModelAgent, DeepAgent, PlanExecuteAgent
  │
Compose (Orchestration Engine)       ← Graph, Chain, Branch, Parallel
  │  Compiles to Runnable[I, O]
  │
Components (Building Block Interfaces) ← Typed interfaces only
  │  ChatModel, Tool, Retriever, Embedder, Indexer, Prompt
  │  (implementations in eino-ext)
  │
Schema (Core Data Types)             ← Message, Document, ToolInfo, StreamReader
  │
Callbacks (Cross-cutting)            ← OnStart, OnEnd, OnError (global or per-invocation)
```

## Guiding Principles

### Always use ADK when building agents

The `flow/` package directory contains older ReAct and multi-agent patterns that predate the ADK. **Always prefer ADK** (`adk.NewChatModelAgent`, `adk.Runner`, prebuilt agents) over `flow/`. The ADK provides checkpoint persistence, streaming, human-in-the-loop, and a richer middleware ecosystem.

### Use Compose directly for simple pipelines

If the user needs a simple linear pipeline (e.g., retrieve → generate) without an agent loop, use `compose.NewGraph` or `compose.NewChain`. Reserve ADK for cases that need the full ReAct turn loop, tool calling, or checkpoint support.

### Generate complete, runnable code

Default to generating complete `main.go` or package files that include imports, error handling, and initialization. Users should be able to copy-paste and run. Always include a `main()` function when generating a standalone program.

### Prefer eino-ext for implementations

Eino core defines only interfaces. For concrete implementations, assume eino-ext:
- **OpenAI**: `github.com/cloudwego/eino-ext/components/model/openai` (for ChatGPT, GPT-4)
- **Ollama**: `github.com/cloudwego/eino-ext/components/model/ollama`
- **ARK**: `github.com/cloudwego/eino-ext/components/model/ark` (ByteDance's ARK platform)
- **Redis**: `github.com/cloudwego/eino-ext/components/retriever/redis`
- **Milvus**: `github.com/cloudwego/eino-ext/components/indexer/milvus`

### Use the Generics API for type safety

Eino provides both typed and type-erased APIs. The typed APIs (prefixed with `Typed*`) use Go generics for type safety. Type-erased aliases exist for backward compatibility. **Always use typed APIs** when generating new code:

```go
// Prefer this:
agent, err := adk.NewTypedChatModelAgent[*schema.Message](ctx, config)

// Over this (type alias):
agent, err := adk.NewChatModelAgent(ctx, config)
```

## Common Code Generation Patterns

When generating code, follow these conventions:

### Import Organization

Group imports by source:
```go
import (
    // stdlib
    "context"
    "fmt"
    "log"
    "os"

    // eino core
    "github.com/cloudwego/eino/adk"
    "github.com/cloudwego/eino/callbacks"
    "github.com/cloudwego/eino/components/model"
    "github.com/cloudwego/eino/components/tool"
    "github.com/cloudwego/eino/compose"
    "github.com/cloudwego/eino/schema"

    // eino-ext (implementations)
    openai "github.com/cloudwego/eino-ext/components/model/openai"
)
```

### Error Handling

Always check errors, wrap with context:
```go
agent, err := adk.NewChatModelAgent(ctx, config)
if err != nil {
    log.Fatalf("failed to create agent: %v", err)
}
```

### Config Patterns

Use inline struct literals for configuration, including all required fields:
```go
model, err := openai.NewChatModel(ctx, &openai.ChatModelConfig{
    APIKey:  os.Getenv("OPENAI_API_KEY"),
    BaseURL: "https://api.openai.com/v1",
    Model:   "gpt-4o",
})
```

### Streaming Output

When generating agent code that streams output, use Runner's event iterator:
```go
iter := runner.Run(ctx, []*schema.Message{
    schema.UserMessage(userPrompt),
})
for iter.Next() {
    event := iter.Value()
    if msg, ok := event.Message(); ok {
        fmt.Print(msg.Content)  // stream to stdout
    }
}
```

## Task: Determine User's Goal

Before generating code, determine which layer and pattern the user needs:

1. **If they mention "agent", "chatbot", "assistant"** → Use ADK (ChatModelAgent + Runner)
2. **If they mention "RAG", "retrieve", "search + generate"** → Use Compose Graph or ADK with a tool
3. **If they mention "tools", "function calling"** → Use ADK with ToolsConfig
4. **If they mention "multi-agent", "orchestration"** → Use DeepAgent or PlanExecuteAgent
5. **If they mention "logging", "tracing", "observe"** → Use Callbacks
6. **If they mention a simple linear flow** → Use Compose Chain

When in doubt, read `references/recipes.md` for the closest matching pattern.
