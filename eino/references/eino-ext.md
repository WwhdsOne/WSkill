# Eino-Ext Reference

Component implementations from the `github.com/cloudwego/eino-ext` repository.
Eino core defines only interfaces; implementations live here.

## Table of Contents

- [Chat Models](#chat-models)
- [Tools](#tools)
- [Retrievers](#retrievers)
- [Indexers](#indexers)
- [Embedders](#embedders)
- [Document Loaders](#document-loaders)

---

## Chat Models

### OpenAI

```go
import openai "github.com/cloudwego/eino-ext/components/model/openai"

model, err := openai.NewChatModel(ctx, &openai.ChatModelConfig{
    APIKey:  os.Getenv("OPENAI_API_KEY"),
    BaseURL: "https://api.openai.com/v1",  // Optional, for proxies
    Model:   "gpt-4o",                      // gpt-4o, gpt-4-turbo, gpt-3.5-turbo, o1-mini, o1, o3-mini
    Temperature: 0.7,                       // Optional (0.0-2.0)
    MaxTokens: 4096,                        // Optional
    Timeout: 60 * time.Second,              // Optional
})
```

**Supported models:** `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `gpt-4`, `gpt-3.5-turbo`, `o1`, `o1-mini`, `o3-mini`, `o1-pro`

**Optional config:**
```go
// Temperature (precision control)
config.Temperature = &tempVal

// Max tokens
config.MaxTokens = &maxTokensVal

// Extra request fields
type ExtraRequest struct {
    ResponseFormat *ResponseFormat // json_object, json_schema, etc.
    ToolChoice     string          // "auto", "none", "required"
    Stop           []string        // Stop sequences
    ParallelToolCalls *bool        // Enable/disable parallel tool calls
}

// Per-call options
openai.WithTemperature(temp float32) openai.Option
openai.WithMaxTokens(maxTokens int) openai.Option
openai.WithModel(model string) openai.Option
openai.WithResponseFormat(format *openai.ResponseFormat) openai.Option
```

### Ollama

```go
import ollama "github.com/cloudwego/eino-ext/components/model/ollama"

model, err := ollama.NewChatModel(ctx, &ollama.ChatModelConfig{
    BaseURL: "http://localhost:11434",
    Model:   "llama3.2",  // llama3.2, mistral, qwen2.5, etc.
    Temperature: 0.7,     // Optional
    MaxTokens: 4096,      // Optional
})
```

**Supported models:** Any model available in your Ollama instance (`llama3.2`, `llama3.1`, `mistral`, `qwen2.5`, `deepseek-r1`, etc.)

### ARK (ByteDance)

```go
import ark "github.com/cloudwego/eino-ext/components/model/ark"

model, err := ark.NewChatModel(ctx, &ark.ChatModelConfig{
    APIKey: os.Getenv("ARK_API_KEY"),
    Model:  "doubao-pro-32k",  // Doubao (豆包) model
})
```

### DeepSeek

```go
import deepseek "github.com/cloudwego/eino-ext/components/model/deepseek"

model, err := deepseek.NewChatModel(ctx, &deepseek.ChatModelConfig{
    APIKey: os.Getenv("DEEPSEEK_API_KEY"),
    Model:  "deepseek-chat",  // or "deepseek-reasoner"
})
```

### Qwen (Tongyi Qianwen)

```go
import qwen "github.com/cloudwego/eino-ext/components/model/qwen"

model, err := qwen.NewChatModel(ctx, &qwen.ChatModelConfig{
    APIKey: os.Getenv("DASHSCOPE_API_KEY"),
    Model:  "qwen-plus",  // qwen-turbo, qwen-plus, qwen-max
})
```

---

## Tools

### Tool Utilities (eino-ext/components/tool/utils)

Convenient tool creation with automatic schema generation.

```go
import toolutils "github.com/cloudwego/eino-ext/components/tool/utils"

type MyToolInput struct {
    Query  string `json:"query" description:"Search query"`
    Limit  int    `json:"limit" description:"Max results" required:"false"`
}

tool, err := toolutils.NewTool(
    &toolutils.ToolConfig{
        Name:        "my_tool",
        Description: "Does something useful.",
        ParamsOneOf: toolutils.ParamsOneOf{
            Params: map[string]*toolutils.ParameterInfo{
                "query": {
                    Type:     "string",
                    Desc:     "Search query",
                    Required: true,
                },
                "limit": {
                    Type:     "number",
                    Desc:     "Max results",
                    Required: false,
                },
            },
        },
    },
    func(ctx context.Context, input string) (string, error) {
        // input is JSON string matching the parameter schema
        var in MyToolInput
        if err := json.Unmarshal([]byte(input), &in); err != nil {
            return "", err
        }
        // Do work...
        return fmt.Sprintf("Results for '%s' (limit: %d)", in.Query, in.Limit), nil
    },
)

// Helper to unmarshal input
func toolutils.UnmarshalInput(v interface{}, input string) error
```

### MCP Tools

Connect to Model Context Protocol servers.

```go
import mcptool "github.com/cloudwego/eino-ext/components/tool/mcp"

tools, err := mcptool.GetTools(ctx, &mcptool.Config{
    Cli:   "npx",
    Args:  []string{"-y", "@modelcontextprotocol/server-filesystem", "/tmp"},
})
```

---

## Retrievers

### Redis Retriever

```go
import redisret "github.com/cloudwego/eino-ext/components/retriever/redis"

retriever, err := redisret.NewRetriever(ctx, &redisret.RetrieverConfig{
    Client:    redisClient,  // *redis.Client
    IndexName: "my_index",
    Embedder:  embedder,     // converts queries to vectors
})
```

### Elasticsearch Retriever

```go
import esret "github.com/cloudwego/eino-ext/components/retriever/es"

retriever, err := esret.NewRetriever(ctx, &esret.RetrieverConfig{
    Client:  esClient,  // *elasticsearch.Client
    Index:   "documents",
    Embedder: embedder,
})
```

### Volc VikingDB Retriever

```go
import vdbret "github.com/cloudwego/eino-ext/components/retriever/volc_vikingdb"

retriever, err := vdbret.NewRetriever(ctx, &vdbret.RetrieverConfig{
    // ByteDance's Volc Engine VikingDB config
})
```

---

## Indexers

### Milvus Indexer

```go
import milvusidx "github.com/cloudwego/eino-ext/components/indexer/milvus"

indexer, err := milvusidx.NewIndexer(ctx, &milvusidx.Config{
    Client:      milvusClient,  // milvus client
    Collection:  "my_collection",
    Embedder:    embedder,
})
```

### Redis Indexer

```go
import redisidx "github.com/cloudwego/eino-ext/components/indexer/redis"

indexer, err := redisidx.NewIndexer(ctx, &redisidx.Config{
    Client:    redisClient,
    IndexName: "my_index",
    Embedder:  embedder,
})
```

### Elasticsearch Indexer

```go
import esidx "github.com/cloudwego/eino-ext/components/indexer/es"

indexer, err := esidx.NewIndexer(ctx, &esidx.Config{
    Client: esClient,
    Index:  "documents",
})
```

---

## Embedders

### OpenAI Embedder

```go
import openaiEmb "github.com/cloudwego/eino-ext/components/embedding/openai"

embedder, err := openaiEmb.NewEmbedder(ctx, &openaiEmb.Config{
    APIKey: os.Getenv("OPENAI_API_KEY"),
    Model:  "text-embedding-3-small",  // or "text-embedding-3-large", "text-embedding-ada-002"
})
```

### Ollama Embedder

```go
import ollamaEmb "github.com/cloudwego/eino-ext/components/embedding/ollama"

embedder, err := ollamaEmb.NewEmbedder(ctx, &ollamaEmb.Config{
    BaseURL: "http://localhost:11434",
    Model:   "nomic-embed-text",
})
```

### ARK Embedder

```go
import arkEmb "github.com/cloudwego/eino-ext/components/embedding/ark"

embedder, err := arkEmb.NewEmbedder(ctx, &arkEmb.Config{
    APIKey: os.Getenv("ARK_API_KEY"),
    Model:  "doubao-embedding",
})
```

---

## Document Loaders

### File Loader

```go
import fileloader "github.com/cloudwego/eino-ext/components/document/loader/file"

loader, err := fileloader.NewFileLoader(ctx, &fileloader.Config{
    Path:     "/path/to/documents",
    UseNameAsID: true,
})
docs, err := loader.Load(ctx)
```

### PDF Loader

```go
import pdfloader "github.com/cloudwego/eino-ext/components/document/loader/pdf"

loader, err := pdfloader.NewPDFLoader(ctx, &pdfloader.Config{
    Path: "/path/to/document.pdf",
})
docs, err := loader.Load(ctx)
```

## General Patterns

### Component Instantiation Pattern

All eino-ext components follow the same pattern:

```go
import comp "github.com/cloudwego/eino-ext/components/<type>/<provider>"

instance, err := comp.New<Type>(ctx, &comp.Config{
    // Provider-specific configuration
})
```

### Provider Abstraction

When generating code that needs to work with multiple providers, import the core interface and use eino-ext for the concrete implementation:

```go
import (
    "github.com/cloudwego/eino/components/model"
    openai "github.com/cloudwego/eino-ext/components/model/openai"
)

var m model.BaseChatModel  // Core interface type

m, err = openai.NewChatModel(ctx, &openai.ChatModelConfig{...})
// Or: m, err = ollama.NewChatModel(ctx, &ollama.ChatModelConfig{...})
```

This pattern works for all component types (Tool, Retriever, Embedder, Indexer, etc.).
