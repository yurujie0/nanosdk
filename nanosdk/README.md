# NanoSDK

🤖 轻量级 Python Agent SDK - 支持工具调用、上下文管理、记忆、Agent Skills 和 Subagent

## ✨ 特性

- **轻量级**: 核心代码简洁，易于理解和扩展
- **工具调用**: 支持定义和执行自定义工具
- **上下文管理**: 会话级别的变量管理和状态共享
- **记忆系统**: 短期和长期记忆支持
- **Agent Skills**: 模块化的技能系统
- **Subagent**: 支持创建和管理子代理
- **异步支持**: 原生支持 async/await

## 📦 安装

```bash
pip install nanosdk
```

## 🚀 快速开始

### 1. 创建 Agent

```python
from nanosdk import Agent, AgentConfig, ModelConfig

config = AgentConfig(
    id="my-agent",
    name="My Agent",
    model=ModelConfig(
        provider="openai",
        model="gpt-4",
        api_key="your-api-key"
    ),
    system_prompt="You are a helpful assistant."
)

agent = Agent(config)
```

### 2. 执行 Agent

```python
# 同步执行
result = await agent.execute("Hello, how are you?")
print(result.output)

# 流式执行
async for chunk in agent.stream("Tell me a story"):
    print(chunk.content, end="")
```

### 3. 定义工具

```python
from nanosdk import Tool, ToolParameterSchema

# 定义计算器工具
calculator = Tool(
    name="calculator",
    description="Perform calculations",
    parameters=ToolParameterSchema(
        properties={
            "expression": {
                "type": "string",
                "description": "Math expression to evaluate"
            }
        },
        required=["expression"]
    ),
    execute=lambda args, ctx: eval(args["expression"])
)

# 注册工具
agent.register_tool(calculator)
```

### 4. 使用记忆

```python
from nanosdk import MemoryStore

# 添加记忆
await agent.memory.add(
    content="User likes Python",
    metadata={"category": "preference"}
)

# 搜索记忆
memories = await agent.memory.search("Python")
```

### 5. 使用 Skills

```python
from nanosdk import Skill

# 创建技能
weather_skill = Skill(
    name="weather",
    description="Get weather information",
    version="1.0.0",
    tools=[get_weather_tool],
    prompts={"system": "You are a weather assistant."}
)

# 注册技能
agent.register_skill(weather_skill)
```

### 6. 使用 Subagent

```python
from nanosdk import SubagentManager

# 创建子代理管理器
subagent_manager = SubagentManager(agent)

# 创建子代理
subagent = await subagent_manager.create(
    id="specialist",
    name="Specialist",
    model=ModelConfig(provider="openai", model="gpt-3.5-turbo"),
    inherit_tools=True
)

# 调用子代理
result = await subagent_manager.call("specialist", "Process this task")
```

## 📚 API 文档

### Agent

```python
class Agent:
    def __init__(self, config: AgentConfig)
    async def execute(self, input: str, context: Optional[ExecutionContext] = None) -> ExecutionResult
    async def stream(self, input: str, context: Optional[ExecutionContext] = None) -> AsyncGenerator[StreamChunk]
    def register_tool(self, tool: Tool) -> None
    def unregister_tool(self, name: str) -> None
    def register_skill(self, skill: Skill) -> None
```

### Context

```python
class ContextManager:
    def create(self, context_id: str, parent_id: Optional[str] = None) -> Context
    def get(self, context_id: str) -> Optional[Context]
    def update(self, context_id: str, variables: Dict[str, Any]) -> None
```

### Memory

```python
class MemoryStore:
    async def add(self, memory: Omit[Memory, 'id' | 'timestamp'>) -> Memory
    async def search(self, query: str, limit: int = 10) -> List[Memory]
    async def get(self, id: str) -> Optional[Memory]
    async def delete(self, id: str) -> None
```

## 🏗️ 架构

```
nanosdk/
├── src/nanosdk/
│   ├── __init__.py      # 入口
│   ├── types.py         # 类型定义
│   ├── agent.py         # Agent 核心
│   ├── context.py       # 上下文管理
│   ├── memory.py        # 记忆系统
│   ├── tool.py          # 工具系统
│   ├── skill.py         # 技能系统
│   └── subagent.py      # 子代理
├── examples/            # 示例代码
└── tests/              # 测试
```

## 📝 License

MIT
