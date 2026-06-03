# Eino Recipes — Common Code Patterns

This file contains complete, runnable code examples for the most common Eino patterns.
Each recipe includes imports, error handling, and a `main()` function.

## Table of Contents

1. [Simple ChatBot (ChatModelAgent + Runner)](#recipe-1-simple-chatbot)
2. [Tool-Calling Agent](#recipe-2-tool-calling-agent)
3. [RAG Pipeline with Graph](#recipe-3-rag-pipeline-with-graph)
4. [RAG with ADK Tool](#recipe-4-rag-with-adk-tool)
5. [Multi-Agent with DeepAgent](#recipe-5-multi-agent-with-deepagent)
6. [Plan-Execute Agent](#recipe-6-plan-execute-agent)
7. [Simple Linear Chain](#recipe-7-simple-linear-chain)
8. [Conditional Branching](#recipe-8-conditional-branching)
9. [Parallel Execution](#recipe-9-parallel-execution)
10. [Observability with Callbacks](#recipe-10-observability-with-callbacks)
11. [Human-in-the-Loop (Interrupt/Resume)](#recipe-11-human-in-the-loop)
12. [Custom Component (Retriever)](#recipe-12-custom-component)
13. [Sub-Agent as Tool](#recipe-13-sub-agent-as-tool)

---

## Recipe 1: Simple ChatBot

A minimal chatbot using ChatModelAgent + Runner.

```go
package main

import (
    "context"
    "fmt"
    "log"
    "os"

    "github.com/cloudwego/eino/adk"
    "github.com/cloudwego/eino/schema"
    openai "github.com/cloudwego/eino-ext/components/model/openai"
)

func main() {
    ctx := context.Background()

    model, err := openai.NewChatModel(ctx, &openai.ChatModelConfig{
        APIKey:  os.Getenv("OPENAI_API_KEY"),
        BaseURL: "https://api.openai.com/v1",
        Model:   "gpt-4o",
    })
    if err != nil {
        log.Fatalf("create model: %v", err)
    }

    agent, err := adk.NewChatModelAgent(ctx, &adk.ChatModelAgentConfig{
        Name:        "assistant",
        Description: "A helpful AI assistant",
        Instruction: "You are a helpful assistant. Be concise and accurate.",
        Model:       model,
    })
    if err != nil {
        log.Fatalf("create agent: %v", err)
    }

    runner := adk.NewRunner(ctx, adk.RunnerConfig{Agent: agent})

    iter := runner.Run(ctx, []*schema.Message{
        schema.UserMessage("What is the capital of France?"),
    })

    for iter.Next() {
        event := iter.Value()
        if msg, ok := event.Message(); ok {
            fmt.Print(msg.Content)
        }
    }
    fmt.Println()
}
```

## Recipe 2: Tool-Calling Agent

An agent that can use tools (web search, calculator).

```go
package main

import (
    "context"
    "encoding/json"
    "fmt"
    "log"
    "os"
    "strconv"
    "strings"

    "github.com/cloudwego/eino/adk"
    "github.com/cloudwego/eino/components/tool"
    "github.com/cloudwego/eino/compose"
    "github.com/cloudwego/eino/schema"

    openai "github.com/cloudwego/eino-ext/components/model/openai"
    toolutils "github.com/cloudwego/eino-ext/components/tool/utils"
)

// CalculatorInput defines the parameters for the calculator tool.
type CalculatorInput struct {
    Expression string `json:"expression" description:"Math expression to evaluate, e.g. '2+3*4'"`
}

func main() {
    ctx := context.Background()

    model, err := openai.NewChatModel(ctx, &openai.ChatModelConfig{
        APIKey:  os.Getenv("OPENAI_API_KEY"),
        Model:   "gpt-4o",
    })
    if err != nil {
        log.Fatalf("create model: %v", err)
    }

    // Define a calculator tool using eino-ext's tool/utils for convenient creation.
    calcTool, err := toolutils.NewTool(
        &toolutils.ToolConfig{
            Name:        "calculator",
            Description: "Evaluate a mathematical expression. Supports +, -, *, /.",
            ParamsOneOf: toolutils.ParamsOneOf{
                Params: map[string]*toolutils.ParameterInfo{
                    "expression": {
                        Type:     "string",
                        Desc:     "Math expression to evaluate",
                        Required: true,
                    },
                },
            },
        },
        func(ctx context.Context, input string) (string, error) {
            var in CalculatorInput
            if err := json.Unmarshal([]byte(input), &in); err != nil {
                return "", err
            }
            // Simple expression evaluator — in production, use a proper parser
            result := evaluateSimpleExpression(in.Expression)
            return fmt.Sprintf("Result: %s = %d", in.Expression, result), nil
        },
    )
    if err != nil {
        log.Fatalf("create calculator tool: %v", err)
    }

    // Define a web search tool (mock implementation).
    searchTool, err := toolutils.NewTool(
        &toolutils.ToolConfig{
            Name:        "web_search",
            Description: "Search the web for information.",
            ParamsOneOf: toolutils.ParamsOneOf{
                Params: map[string]*toolutils.ParameterInfo{
                    "query": {Type: "string", Desc: "Search query", Required: true},
                },
            },
        },
        func(ctx context.Context, input string) (string, error) {
            var in struct{ Query string `json:"query"` }
            json.Unmarshal([]byte(input), &in)
            return fmt.Sprintf("Mock search result for: %s", in.Query), nil
        },
    )
    if err != nil {
        log.Fatalf("create search tool: %v", err)
    }

    agent, err := adk.NewChatModelAgent(ctx, &adk.ChatModelAgentConfig{
        Name:        "tool-agent",
        Description: "An agent that can search and calculate",
        Instruction: "You are a helpful assistant with tools. Use them when needed.",
        Model:       model,
        ToolsConfig: adk.ToolsConfig{
            ToolsNodeConfig: compose.ToolsNodeConfig{
                Tools: []tool.BaseTool{searchTool, calcTool},
            },
        },
        MaxIterations: 10,
    })
    if err != nil {
        log.Fatalf("create agent: %v", err)
    }

    runner := adk.NewRunner(ctx, adk.RunnerConfig{Agent: agent})

    iter := runner.Run(ctx, []*schema.Message{
        schema.UserMessage("What is 123 * 456?"),
    })

    for iter.Next() {
        event := iter.Value()
        if msg, ok := event.Message(); ok {
            fmt.Print(msg.Content)
        }
    }
    fmt.Println()
}

func evaluateSimpleExpression(expr string) int {
    // Stub — replace with a proper evaluator in production
    parts := strings.Fields(expr)
    if len(parts) >= 3 {
        a, _ := strconv.Atoi(parts[0])
        b, _ := strconv.Atoi(parts[2])
        switch parts[1] {
        case "+": return a + b
        case "-": return a - b
        case "*": return a * b
        case "/": return a / b
        }
    }
    return 0
}
```

## Recipe 3: RAG Pipeline with Graph

A retrieval-augmented generation pipeline using compose.Graph.

```go
package main

import (
    "context"
    "fmt"
    "log"
    "os"

    "github.com/cloudwego/eino/components/model"
    "github.com/cloudwego/eino/components/prompt"
    "github.com/cloudwego/eino/components/retriever"
    "github.com/cloudwego/eino/compose"
    "github.com/cloudwego/eino/schema"

    openai "github.com/cloudwego/eino-ext/components/model/openai"
)

func main() {
    ctx := context.Background()

    model, err := openai.NewChatModel(ctx, &openai.ChatModelConfig{
        APIKey:  os.Getenv("OPENAI_API_KEY"),
        Model:   "gpt-4o",
    })
    if err != nil {
        log.Fatalf("create model: %v", err)
    }

    // Assume a retriever is created elsewhere (see Recipe 12 for custom retriever).
    // For this example, use a mock retriever via compose.InvokableLambda.
    mockRetriever := compose.InvokableLambda(
        func(ctx context.Context, query string) ([]*schema.Document, error) {
            return []*schema.Document{
                {Content: "Eino is ByteDance's Go framework for LLM applications."},
                {Content: "It provides ADK, Compose, Components, and Schema layers."},
            }, nil
        },
    )

    // Create a prompt template that combines context and query.
    tmpl, err := prompt.FromMessages(
        schema.FString,
        schema.SystemMessage("Answer based on the following context:\n\n{context}"),
        schema.UserMessage("{query}"),
    )
    if err != nil {
        log.Fatalf("create template: %v", err)
    }

    // Build the graph: START → retriever → (format context) → llm → END
    graph := compose.NewGraph[map[string]any, *schema.Message]()

    _ = graph.AddRetrieverNode("retrieve", mockRetriever)
    _ = graph.AddChatTemplateNode("prompt", tmpl)
    _ = graph.AddChatModelNode("llm", model)

    _ = graph.AddEdge(compose.START, "retrieve")
    _ = graph.AddEdge("retrieve", "prompt")
    _ = graph.AddEdge("prompt", "llm")
    _ = graph.AddEdge("llm", compose.END)

    runnable, err := graph.Compile(ctx)
    if err != nil {
        log.Fatalf("compile graph: %v", err)
    }

    result, err := runnable.Invoke(ctx, map[string]any{
        "query": "What is Eino?",
    })
    if err != nil {
        log.Fatalf("invoke: %v", err)
    }

    fmt.Println(result.Content)
}
```

## Recipe 4: RAG with ADK Tool

RAG as a tool that an agent can invoke.

```go
package main

import (
    "context"
    "fmt"
    "log"
    "os"
    "strings"

    "github.com/cloudwego/eino/adk"
    "github.com/cloudwego/eino/compose"
    "github.com/cloudwego/eino/schema"

    openai "github.com/cloudwego/eino-ext/components/model/openai"
    toolutils "github.com/cloudwego/eino-ext/components/tool/utils"
)

func main() {
    ctx := context.Background()

    model, err := openai.NewChatModel(ctx, &openai.ChatModelConfig{
        APIKey:  os.Getenv("OPENAI_API_KEY"),
        Model:   "gpt-4o",
    })
    if err != nil {
        log.Fatalf("create model: %v", err)
    }

    // Knowledge base to search.
    knowledgeBase := map[string]string{
        "eino":     "Eino is ByteDance's Go LLM application framework.",
        "cloudwego": "CloudWeGo is ByteDance's open-source microservice ecosystem.",
        "adk":      "ADK (Agent Development Kit) provides agent runtime in Eino.",
    }

    // Create a RAG tool that searches the knowledge base.
    ragTool, err := toolutils.NewTool(
        &toolutils.ToolConfig{
            Name:        "knowledge_search",
            Description: "Search the knowledge base for information about Eino and CloudWeGo.",
            ParamsOneOf: toolutils.ParamsOneOf{
                Params: map[string]*toolutils.ParameterInfo{
                    "query": {Type: "string", Desc: "Search query", Required: true},
                },
            },
        },
        func(ctx context.Context, input string) (string, error) {
            var in struct{ Query string `json:"query"` }
            toolutils.UnmarshalInput(&in, input)
            query := strings.ToLower(in.Query)
            var results []string
            for key, val := range knowledgeBase {
                if strings.Contains(key, query) || strings.Contains(strings.ToLower(val), query) {
                    results = append(results, fmt.Sprintf("[%s]: %s", key, val))
                }
            }
            if len(results) == 0 {
                return "No relevant information found.", nil
            }
            return strings.Join(results, "\n"), nil
        },
    )
    if err != nil {
        log.Fatalf("create rag tool: %v", err)
    }

    agent, err := adk.NewChatModelAgent(ctx, &adk.ChatModelAgentConfig{
        Name:        "rag-agent",
        Description: "An assistant with access to a knowledge base",
        Instruction: "You answer questions using the knowledge_search tool to look up information.",
        Model:       model,
        ToolsConfig: adk.ToolsConfig{
            ToolsNodeConfig: compose.ToolsNodeConfig{
                Tools: []interface{}{ragTool},
            },
        },
    })
    if err != nil {
        log.Fatalf("create agent: %v", err)
    }

    runner := adk.NewRunner(ctx, adk.RunnerConfig{Agent: agent})

    iter := runner.Run(ctx, []*schema.Message{
        schema.UserMessage("Tell me about ADK in Eino."),
    })

    for iter.Next() {
        event := iter.Value()
        if msg, ok := event.Message(); ok {
            fmt.Print(msg.Content)
        }
    }
    fmt.Println()
}
```

## Recipe 5: Multi-Agent with DeepAgent

Two specialized agents orchestrated by DeepAgent.

```go
package main

import (
    "context"
    "fmt"
    "log"
    "os"

    "github.com/cloudwego/eino/adk"
    "github.com/cloudwego/eino/adk/prebuilt/deep"
    "github.com/cloudwego/eino/compose"
    "github.com/cloudwego/eino/schema"

    openai "github.com/cloudwego/eino-ext/components/model/openai"
    toolutils "github.com/cloudwego/eino-ext/components/tool/utils"
)

func main() {
    ctx := context.Background()

    model, err := openai.NewChatModel(ctx, &openai.ChatModelConfig{
        APIKey:  os.Getenv("OPENAI_API_KEY"),
        Model:   "gpt-4o",
    })
    if err != nil {
        log.Fatalf("create model: %v", err)
    }

    // Sub-agent 1: Research specialist
    researchTool, _ := toolutils.NewTool(
        &toolutils.ToolConfig{
            Name:        "research",
            Description: "Research a topic and provide findings.",
            ParamsOneOf: toolutils.ParamsOneOf{
                Params: map[string]*toolutils.ParameterInfo{
                    "topic": {Type: "string", Desc: "Topic to research", Required: true},
                },
            },
        },
        func(ctx context.Context, input string) (string, error) {
            var in struct{ Topic string `json:"topic"` }
            toolutils.UnmarshalInput(&in, input)
            return fmt.Sprintf("Research findings for '%s': [detailed analysis here]", in.Topic), nil
        },
    )

    researchAgent, err := adk.NewChatModelAgent(ctx, &adk.ChatModelAgentConfig{
        Name:        "researcher",
        Description: "Expert at researching topics and providing detailed findings",
        Instruction: "You are a research specialist. Use your research tool to find information.",
        Model:       model,
        ToolsConfig: adk.ToolsConfig{
            ToolsNodeConfig: compose.ToolsNodeConfig{
                Tools: []interface{}{researchTool},
            },
        },
    })
    if err != nil {
        log.Fatalf("create research agent: %v", err)
    }

    // Sub-agent 2: Writer
    writerAgent, err := adk.NewChatModelAgent(ctx, &adk.ChatModelAgentConfig{
        Name:        "writer",
        Description: "Expert at writing well-structured content based on research",
        Instruction: "You are a professional writer. Write clear, engaging content based on provided information.",
        Model:       model,
    })
    if err != nil {
        log.Fatalf("create writer agent: %v", err)
    }

    // Orchestrator using DeepAgent
    deepAgent, err := deep.New(ctx, &deep.Config{
        Name:      "orchestrator",
        Model:     model,
        SubAgents: []adk.Agent{researchAgent, writerAgent},
    })
    if err != nil {
        log.Fatalf("create deep agent: %v", err)
    }

    runner := adk.NewRunner(ctx, adk.RunnerConfig{Agent: deepAgent})

    iter := runner.Run(ctx, []*schema.Message{
        schema.UserMessage("Research the history of Go programming language and write a summary."),
    })

    for iter.Next() {
        event := iter.Value()
        if msg, ok := event.Message(); ok {
            fmt.Print(msg.Content)
        }
    }
    fmt.Println()
}
```

## Recipe 6: Plan-Execute Agent

An agent that creates a plan first, then executes it step by step.

```go
package main

import (
    "context"
    "fmt"
    "log"
    "os"

    "github.com/cloudwego/eino/adk"
    "github.com/cloudwego/eino/adk/prebuilt/planexecute"
    "github.com/cloudwego/eino/compose"
    "github.com/cloudwego/eino/schema"

    openai "github.com/cloudwego/eino-ext/components/model/openai"
    toolutils "github.com/cloudwego/eino-ext/components/tool/utils"
)

func main() {
    ctx := context.Background()

    model, err := openai.NewChatModel(ctx, &openai.ChatModelConfig{
        APIKey:  os.Getenv("OPENAI_API_KEY"),
        Model:   "gpt-4o",
    })
    if err != nil {
        log.Fatalf("create model: %v", err)
    }

    // Planner model (can use a reasoning model like o1 for better planning)
    planner, err := openai.NewChatModel(ctx, &openai.ChatModelConfig{
        APIKey: os.Getenv("OPENAI_API_KEY"),
        Model:  "o1-mini",
    })
    if err != nil {
        log.Fatalf("create planner: %v", err)
    }

    // Tools available to the executor
    searchTool, _ := toolutils.NewTool(
        &toolutils.ToolConfig{
            Name:        "search",
            Description: "Search for information.",
            ParamsOneOf: toolutils.ParamsOneOf{
                Params: map[string]*toolutils.ParameterInfo{
                    "query": {Type: "string", Desc: "Search query", Required: true},
                },
            },
        },
        func(ctx context.Context, input string) (string, error) {
            var in struct{ Query string `json:"query"` }
            toolutils.UnmarshalInput(&in, input)
            return fmt.Sprintf("Search results for '%s'", in.Query), nil
        },
    )

    planAgent, err := planexecute.New(ctx, &planexecute.Config{
        Name:        "planner-executor",
        Description: "Plans and executes multi-step tasks",
        Planner:     planner,
        Executor:    model,
        Tools: []interface{}{searchTool},
    })
    if err != nil {
        log.Fatalf("create plan-execute agent: %v", err)
    }

    runner := adk.NewRunner(ctx, adk.RunnerConfig{Agent: planAgent})

    iter := runner.Run(ctx, []*schema.Message{
        schema.UserMessage("Compare Python and Go for web development. List pros and cons."),
    })

    for iter.Next() {
        event := iter.Value()
        if msg, ok := event.Message(); ok {
            fmt.Print(msg.Content)
        }
    }
    fmt.Println()
}
```

## Recipe 7: Simple Linear Chain

A linear processing chain using compose.Chain.

```go
package main

import (
    "context"
    "fmt"
    "log"
    "os"

    "github.com/cloudwego/eino/compose"
    "github.com/cloudwego/eino/schema"

    openai "github.com/cloudwego/eino-ext/components/model/openai"
)

func main() {
    ctx := context.Background()

    model, err := openai.NewChatModel(ctx, &openai.ChatModelConfig{
        APIKey:  os.Getenv("OPENAI_API_KEY"),
        Model:   "gpt-4o",
    })
    if err != nil {
        log.Fatalf("create model: %v", err)
    }

    // Create a chain: translate → summarize
    chain := compose.NewChain[[]*schema.Message, *schema.Message]()

    // Step 1: Translation lambda
    chain.AppendLambda(
        compose.InvokableLambda(func(ctx context.Context, msgs []*schema.Message) ([]*schema.Message, error) {
            instruction := schema.SystemMessage("Translate the following text to English.")
            return append([]*schema.Message{instruction}, msgs...), nil
        }),
    )

    // Step 2: Summarize with LLM
    chain.AppendChatModel(model)

    // Step 3: Extract summary
    chain.AppendLambda(
        compose.InvokableLambda(func(ctx context.Context, msg *schema.Message) (*schema.Message, error) {
            summary := "Summary: " + msg.Content[:min(len(msg.Content), 200)]
            return &schema.Message{Role: schema.Assistant, Content: summary}, nil
        }),
    )

    runnable, err := chain.Compile(ctx)
    if err != nil {
        log.Fatalf("compile chain: %v", err)
    }

    result, err := runnable.Invoke(ctx, []*schema.Message{
        schema.SystemMessage("Translate to English:"),
        schema.UserMessage("Bonjour le monde! Comment ça va?"),
    })
    if err != nil {
        log.Fatalf("invoke: %v", err)
    }

    fmt.Println(result.Content)
}

func min(a, b int) int {
    if a < b { return a }
    return b
}
```

## Recipe 8: Conditional Branching

Route input to different processing paths based on content.

```go
package main

import (
    "context"
    "fmt"
    "log"
    "os"
    "strings"

    "github.com/cloudwego/eino/compose"
    "github.com/cloudwego/eino/schema"

    openai "github.com/cloudwego/eino-ext/components/model/openai"
)

func main() {
    ctx := context.Background()

    model, err := openai.NewChatModel(ctx, &openai.ChatModelConfig{
        APIKey:  os.Getenv("OPENAI_API_KEY"),
        Model:   "gpt-4o",
    })
    if err != nil {
        log.Fatalf("create model: %v", err)
    }

    graph := compose.NewGraph[[]*schema.Message, *schema.Message]()

    // Classifier lambda — determines which path to take
    _ = graph.AddLambdaNode("classifier",
        compose.InvokableLambda(func(ctx context.Context, msgs []*schema.Message) ([]*schema.Message, error) {
            return msgs, nil
        }),
    )

    // Three specialized processor lambdas
    _ = graph.AddLambdaNode("process_code",
        compose.InvokableLambda(func(ctx context.Context, msgs []*schema.Message) (*schema.Message, error) {
            return &schema.Message{
                Role:    schema.Assistant,
                Content: fmt.Sprintf("[CODE] Processed: %s", msgs[len(msgs)-1].Content),
            }, nil
        }),
    )

    _ = graph.AddLambdaNode("process_general", model)

    _ = graph.AddLambdaNode("process_summary",
        compose.InvokableLambda(func(ctx context.Context, msgs []*schema.Message) (*schema.Message, error) {
            return &schema.Message{
                Role:    schema.Assistant,
                Content: fmt.Sprintf("[SUMMARY] TL;DR: %s", msgs[len(msgs)-1].Content),
            }, nil
        }),
    )

    // Routing condition
    _ = graph.AddBranch("classifier", compose.NewGraphBranch(
        func(ctx context.Context, msgs []*schema.Message) (string, error) {
            text := strings.ToLower(msgs[len(msgs)-1].Content)
            if strings.Contains(text, "code") || strings.Contains(text, "program") {
                return "process_code", nil
            }
            if strings.Contains(text, "summarize") || strings.Contains(text, "tl;dr") {
                return "process_summary", nil
            }
            return "process_general", nil
        },
        map[string]bool{
            "process_code":    true,
            "process_general": true,
            "process_summary": true,
        },
    ))

    _ = graph.AddEdge(compose.START, "classifier")
    _ = graph.AddEdge("process_code", compose.END)
    _ = graph.AddEdge("process_general", compose.END)
    _ = graph.AddEdge("process_summary", compose.END)

    runnable, err := graph.Compile(ctx)
    if err != nil {
        log.Fatalf("compile: %v", err)
    }

    result, err := runnable.Invoke(ctx, []*schema.Message{
        schema.UserMessage("Can you help me with a Go code problem?"),
    })
    if err != nil {
        log.Fatalf("invoke: %v", err)
    }
    fmt.Println(result.Content)
}
```

## Recipe 9: Parallel Execution

Run multiple operations concurrently and combine results.

```go
package main

import (
    "context"
    "fmt"
    "log"
    "os"

    "github.com/cloudwego/eino/compose"
    "github.com/cloudwego/eino/schema"

    openai "github.com/cloudwego/eino-ext/components/model/openai"
)

func main() {
    ctx := context.Background()

    graph := compose.NewGraph[string, string]()

    _ = graph.AddLambdaNode("extract_keywords",
        compose.InvokableLambda(func(ctx context.Context, text string) (string, error) {
            return fmt.Sprintf("Keywords: [eino, golang, framework]"), nil
        }),
    )

    _ = graph.AddLambdaNode("count_tokens",
        compose.InvokableLambda(func(ctx context.Context, text string) (string, error) {
            return fmt.Sprintf("Tokens: %d", len(text)/4), nil
        }),
    )

    // Combine results
    _ = graph.AddLambdaNode("merge",
        compose.InvokableLambda(func(ctx context.Context, inputs map[string]any) (string, error) {
            kw := inputs["extract_keywords"].(string)
            ct := inputs["count_tokens"].(string)
            return fmt.Sprintf("Analysis:\n- %s\n- %s", kw, ct), nil
        }),
    )

    _ = graph.AddEdge(compose.START, "extract_keywords")
    _ = graph.AddEdge(compose.START, "count_tokens")
    _ = graph.AddEdge("extract_keywords", "merge")
    _ = graph.AddEdge("count_tokens", "merge")
    _ = graph.AddEdge("merge", compose.END)

    runnable, err := graph.Compile(ctx)
    if err != nil {
        log.Fatalf("compile: %v", err)
    }

    result, err := runnable.Invoke(ctx, "Eino is a Go framework for building LLM applications...")
    if err != nil {
        log.Fatalf("invoke: %v", err)
    }
    fmt.Println(result)
}
```

## Recipe 10: Observability with Callbacks

Add logging and tracing to agent execution.

```go
package main

import (
    "context"
    "fmt"
    "log"
    "os"
    "time"

    "github.com/cloudwego/eino/adk"
    "github.com/cloudwego/eino/callbacks"
    "github.com/cloudwego/eino/schema"

    openai "github.com/cloudwego/eino-ext/components/model/openai"
)

func main() {
    ctx := context.Background()

    // Build an observability handler
    handler := callbacks.NewHandlerBuilder().
        OnStartFn(func(ctx context.Context, info *callbacks.RunInfo, input callbacks.CallbackInput) context.Context {
            startTime := time.Now()
            log.Printf("[START] %s (type=%s)", info.Name, info.Type)
            return context.WithValue(ctx, "start_time", startTime)
        }).
        OnEndFn(func(ctx context.Context, info *callbacks.RunInfo, output callbacks.CallbackOutput) context.Context {
            if start, ok := ctx.Value("start_time").(time.Time); ok {
                log.Printf("[END] %s — took %v", info.Name, time.Since(start))
            }
            return ctx
        }).
        OnErrorFn(func(ctx context.Context, info *callbacks.RunInfo, err error) context.Context {
            log.Printf("[ERROR] %s — %v", info.Name, err)
            return ctx
        }).
        Build()

    // Register as global handler (call at startup, not thread-safe after)
    callbacks.AppendGlobalHandlers(handler)

    model, err := openai.NewChatModel(ctx, &openai.ChatModelConfig{
        APIKey:  os.Getenv("OPENAI_API_KEY"),
        Model:   "gpt-4o",
    })
    if err != nil {
        log.Fatalf("create model: %v", err)
    }

    agent, err := adk.NewChatModelAgent(ctx, &adk.ChatModelAgentConfig{
        Name:        "observed-agent",
        Description: "An agent with observability",
        Instruction: "You are a helpful assistant.",
        Model:       model,
    })
    if err != nil {
        log.Fatalf("create agent: %v", err)
    }

    runner := adk.NewRunner(ctx, adk.RunnerConfig{Agent: agent})

    iter := runner.Run(ctx, []*schema.Message{
        schema.UserMessage("Say hello in 3 languages."),
    })

    for iter.Next() {
        event := iter.Value()
        if msg, ok := event.Message(); ok {
            fmt.Print(msg.Content)
        }
    }
    fmt.Println()
}
```

## Recipe 11: Human-in-the-Loop

An agent that can pause for human approval before executing tools.

```go
package main

import (
    "context"
    "fmt"
    "log"
    "os"

    "github.com/cloudwego/eino/adk"
    "github.com/cloudwego/eino/compose"
    "github.com/cloudwego/eino/schema"

    openai "github.com/cloudwego/eino-ext/components/model/openai"
    toolutils "github.com/cloudwego/eino-ext/components/tool/utils"
)

// NOTE: For brevity, this recipe shows the conceptual pattern.
// In a real application, you would:
// 1. Run the agent until it interrupts
// 2. Save the checkpoint ID
// 3. Present the interrupt to the user
// 4. Resume with user's input

func main() {
    ctx := context.Background()

    model, err := openai.NewChatModel(ctx, &openai.ChatModelConfig{
        APIKey:  os.Getenv("OPENAI_API_KEY"),
        Model:   "gpt-4o",
    })
    if err != nil {
        log.Fatalf("create model: %v", err)
    }

    // A tool that requires approval before running.
    // In a real scenario, use InterruptAndWait for human input.
    sendEmailTool, _ := toolutils.NewTool(
        &toolutils.ToolConfig{
            Name:        "send_email",
            Description: "Send an email (requires approval).",
            ParamsOneOf: toolutils.ParamsOneOf{
                Params: map[string]*toolutils.ParameterInfo{
                    "to":      {Type: "string", Desc: "Recipient", Required: true},
                    "subject": {Type: "string", Desc: "Subject", Required: true},
                    "body":    {Type: "string", Desc: "Email body", Required: true},
                },
            },
        },
        func(ctx context.Context, input string) (string, error) {
            // Interrupt to ask for human approval
            err := adk.InterruptAndWait(ctx, map[string]any{
                "action":  "approve_email",
                "message": "Please approve sending this email",
            })
            if err != nil {
                return "", err
            }
            // After resume, check approval
            data := adk.GetResumeData(ctx)
            if approved, _ := data["approved"].(bool); approved {
                return "Email sent successfully.", nil
            }
            return "Email sending cancelled by user.", nil
        },
    )

    agent, err := adk.NewChatModelAgent(ctx, &adk.ChatModelAgentConfig{
        Name:        "email-agent",
        Description: "An agent that sends emails with human approval",
        Instruction: "You help compose and send emails. Always confirm before sending.",
        Model:       model,
        ToolsConfig: adk.ToolsConfig{
            ToolsNodeConfig: compose.ToolsNodeConfig{
                Tools: []interface{}{sendEmailTool},
            },
        },
    })
    if err != nil {
        log.Fatalf("create agent: %v", err)
    }

    runner := adk.NewRunner(ctx, adk.RunnerConfig{
        Agent: agent,
        // Enable checkpointing for resume support
        EnableCheckPoint: true,
    })

    // First run — agent will reach the email tool and interrupt.
    iter := runner.Run(ctx, []*schema.Message{
        schema.UserMessage("Send an email to john@example.com with subject 'Hello' and body 'Hi John!'"),
    })

    for iter.Next() {
        event := iter.Value()
        if event.Action != nil && event.Action.Interrupted != nil {
            // Tool interrupted — save checkpoint, ask user.
            checkpointID := runner.CheckPointID()
            fmt.Printf("Interrupted! Checkpoint: %s\n", checkpointID)
            fmt.Printf("Data: %v\n", event.Action.Interrupted.Data)

            // In production, present this to the user and resume later:
            // runner.Resume(ctx, checkpointID, map[string]any{"approved": true})
            return
        }
        if msg, ok := event.Message(); ok {
            fmt.Print(msg.Content)
        }
    }
    fmt.Println()
}
```

## Recipe 12: Custom Component

Implement a custom retriever by satisfying the interface.

```go
package main

import (
    "context"
    "fmt"
    "strings"
    "sync"

    "github.com/cloudwego/eino/components/retriever"
    "github.com/cloudwego/eino/schema"
)

// InMemoryRetriever implements retriever.Retriever with an in-memory store.
type InMemoryRetriever struct {
    mu         sync.RWMutex
    documents  []*schema.Document
}

// NewInMemoryRetriever creates a new in-memory retriever.
func NewInMemoryRetriever(docs []*schema.Document) *InMemoryRetriever {
    return &InMemoryRetriever{documents: docs}
}

// Add adds documents to the retriever.
func (r *InMemoryRetriever) Add(docs ...*schema.Document) {
    r.mu.Lock()
    defer r.mu.Unlock()
    r.documents = append(r.documents, docs...)
}

// Retrieve satisfies the retriever.Retriever interface.
func (r *InMemoryRetriever) Retrieve(ctx context.Context, query string, opts ...retriever.Option) ([]*schema.Document, error) {
    r.mu.RLock()
    defer r.mu.RUnlock()

    query = strings.ToLower(query)
    var results []*schema.Document

    for _, doc := range r.documents {
        if strings.Contains(strings.ToLower(doc.Content), query) {
            results = append(results, doc)
        }
    }
    return results, nil
}

// Usage example:
func main() {
    retriever := NewInMemoryRetriever([]*schema.Document{
        {Content: "Eino is a Go framework for LLM applications."},
        {Content: "Go was created at Google in 2009."},
        {Content: "CloudWeGo is ByteDance's microservice ecosystem."},
    })

    docs, err := retriever.Retrieve(context.Background(), "eino")
    if err != nil {
        fmt.Printf("Error: %v\n", err)
        return
    }

    for _, doc := range docs {
        fmt.Printf("- %s (score: %.2f)\n", doc.Content, doc.Score)
    }
}
```

## Recipe 13: Sub-Agent as Tool

Wrap one agent as a tool that another agent can call.

```go
package main

import (
    "context"
    "fmt"
    "log"
    "os"

    "github.com/cloudwego/eino/adk"
    "github.com/cloudwego/eino/compose"
    "github.com/cloudwego/eino/schema"

    openai "github.com/cloudwego/eino-ext/components/model/openai"
)

func main() {
    ctx := context.Background()

    model, err := openai.NewChatModel(ctx, &openai.ChatModelConfig{
        APIKey:  os.Getenv("OPENAI_API_KEY"),
        Model:   "gpt-4o",
    })
    if err != nil {
        log.Fatalf("create model: %v", err)
    }

    // Sub-agent: specialized in math
    mathAgent, err := adk.NewChatModelAgent(ctx, &adk.ChatModelAgentConfig{
        Name:        "math-expert",
        Description: "Expert at solving math problems and calculations",
        Instruction: "You are a math expert. Solve mathematical problems step by step.",
        Model:       model,
    })
    if err != nil {
        log.Fatalf("create math agent: %v", err)
    }

    // Wrap the sub-agent as a tool
    mathTool, err := adk.NewAgentTool(ctx, mathAgent,
        adk.WithAgentToolDescription("Use this tool for mathematical calculations and problem solving."),
    )
    if err != nil {
        log.Fatalf("create agent tool: %v", err)
    }

    // Main orchestrator agent
    mainAgent, err := adk.NewChatModelAgent(ctx, &adk.ChatModelAgentConfig{
        Name:        "orchestrator",
        Description: "Main agent that delegates to specialists",
        Instruction: "You are a helpful assistant. For math problems, delegate to the math-expert tool.",
        Model:       model,
        ToolsConfig: adk.ToolsConfig{
            ToolsNodeConfig: compose.ToolsNodeConfig{
                Tools: []interface{}{mathTool},
            },
        },
    })
    if err != nil {
        log.Fatalf("create main agent: %v", err)
    }

    runner := adk.NewRunner(ctx, adk.RunnerConfig{Agent: mainAgent})

    iter := runner.Run(ctx, []*schema.Message{
        schema.UserMessage("What is the square root of 144?"),
    })

    for iter.Next() {
        event := iter.Value()
        if msg, ok := event.Message(); ok {
            fmt.Print(msg.Content)
        }
    }
    fmt.Println()
}
```
