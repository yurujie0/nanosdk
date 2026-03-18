"""
ReAct Agent 测试用例

测试 ReAct 范式的核心功能：
1. 基本执行流程
2. 工具调用循环
3. 多轮迭代
4. 消息历史维护
5. 错误处理
"""

import asyncio
import pytest
from datetime import datetime
from typing import Any, List

from nanosdk import (
    Agent,
    AgentConfig,
    ModelConfig,
    Tool,
    ToolParameterSchema,
    ToolContext,
    ExecutionContext,
    AgentStatus,
    MessageRole,
)


# ============================================================================
# 测试工具定义
# ============================================================================

def create_calculator_tool() -> Tool:
    """创建计算器工具"""
    def execute(args: dict, ctx: ToolContext) -> str:
        expression = args.get("expression", "")
        try:
            # 安全计算 - 只允许基本数学运算
            allowed_names = {"abs": abs, "round": round, "max": max, "min": min}
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"
    
    return Tool(
        name="calculator",
        description="Perform mathematical calculations",
        parameters=ToolParameterSchema(
            properties={
                "expression": {
                    "type": "string",
                    "description": "Math expression to evaluate, e.g., '2 + 2'"
                }
            },
            required=["expression"]
        ),
        execute=execute
    )


def create_search_tool() -> Tool:
    """创建搜索工具（模拟）"""
    async def execute(args: dict, ctx: ToolContext) -> str:
        query = args.get("query", "")
        # 模拟搜索延迟
        await asyncio.sleep(0.01)
        return f"Search results for: {query}\n1. Result A\n2. Result B"
    
    return Tool(
        name="search",
        description="Search for information",
        parameters=ToolParameterSchema(
            properties={
                "query": {
                    "type": "string",
                    "description": "Search query"
                }
            },
            required=["query"]
        ),
        execute=execute
    )


def create_weather_tool() -> Tool:
    """创建天气工具"""
    def execute(args: dict, ctx: ToolContext) -> str:
        location = args.get("location", "")
        return f"Weather in {location}: Sunny, 25°C"
    
    return Tool(
        name="weather",
        description="Get weather information for a location",
        parameters=ToolParameterSchema(
            properties={
                "location": {
                    "type": "string",
                    "description": "City or location name"
                }
            },
            required=["location"]
        ),
        execute=execute
    )


def create_failing_tool() -> Tool:
    """创建会失败的工具（用于错误测试）"""
    def execute(args: dict, ctx: ToolContext) -> str:
        raise RuntimeError("Tool execution failed")
    
    return Tool(
        name="failing_tool",
        description="A tool that always fails",
        parameters=ToolParameterSchema(
            properties={
                "input": {
                    "type": "string",
                    "description": "Any input"
                }
            },
            required=["input"]
        ),
        execute=execute
    )


# ============================================================================
# 测试夹具
# ============================================================================

@pytest.fixture
def basic_config() -> AgentConfig:
    """基础 Agent 配置"""
    return AgentConfig(
        id="test-agent",
        name="Test Agent",
        model=ModelConfig(
            provider="openai",
            model="gpt-4",
            api_key="test-key"
        ),
        system_prompt="You are a helpful assistant.",
        max_iterations=5
    )


@pytest.fixture
def agent_with_tools(basic_config) -> Agent:
    """带有工具的 Agent"""
    config = basic_config
    config.tools = [create_calculator_tool(), create_search_tool()]
    return Agent(config)


# ============================================================================
# 基础功能测试
# ============================================================================

@pytest.mark.asyncio
async def test_agent_initialization(basic_config):
    """测试 Agent 初始化"""
    agent = Agent(basic_config)
    
    assert agent.config.id == "test-agent"
    assert agent.config.name == "Test Agent"
    assert agent.status == AgentStatus.IDLE
    assert len(agent.list_tools()) == 0


@pytest.mark.asyncio
async def test_tool_registration(basic_config):
    """测试工具注册"""
    agent = Agent(basic_config)
    calculator = create_calculator_tool()
    
    # 注册工具
    agent.register_tool(calculator)
    assert len(agent.list_tools()) == 1
    assert agent.get_tool("calculator") is not None
    
    # 注销工具
    agent.unregister_tool("calculator")
    assert len(agent.list_tools()) == 0
    assert agent.get_tool("calculator") is None


@pytest.mark.asyncio
async def test_agent_status_transitions(basic_config):
    """测试 Agent 状态转换"""
    agent = Agent(basic_config)
    
    # 初始状态
    assert agent.status == AgentStatus.IDLE
    
    # 暂停（从 IDLE 无效）
    agent.pause()
    assert agent.status == AgentStatus.IDLE  # 应该保持不变
    
    # 恢复（从 IDLE 无效）
    agent.resume()
    assert agent.status == AgentStatus.IDLE


# ============================================================================
# ReAct 循环测试
# ============================================================================

@pytest.mark.asyncio
async def test_react_execution_no_tools(basic_config):
    """测试无工具调用的 ReAct 执行"""
    agent = Agent(basic_config)
    
    result = await agent.execute("Hello")
    
    assert result.output is not None
    assert len(result.tool_calls) == 0
    assert len(result.tool_results) == 0
    assert result.metadata.iterations == 1
    assert result.duration >= 0
    assert agent.status == AgentStatus.IDLE


@pytest.mark.asyncio
async def test_react_execution_with_tools(agent_with_tools):
    """测试带工具的 ReAct 执行"""
    agent = agent_with_tools
    
    result = await agent.execute("Calculate 2 + 2")
    
    assert result.output is not None
    assert result.metadata.iterations >= 1
    assert result.duration >= 0
    assert agent.status == AgentStatus.IDLE


@pytest.mark.asyncio
async def test_react_max_iterations(basic_config):
    """测试最大迭代次数限制"""
    config = basic_config
    config.max_iterations = 2
    agent = Agent(config)
    
    result = await agent.execute("Test query")
    
    # 即使没有工具调用，也应该在合理范围内完成
    assert result.metadata.iterations >= 1


@pytest.mark.asyncio
async def test_react_progress_callback(basic_config):
    """测试进度回调"""
    agent = Agent(basic_config)
    progress_logs: List[str] = []
    
    async def on_progress(text: str):
        progress_logs.append(text)
    
    result = await agent.execute("Hello", on_progress=on_progress)
    
    assert result.output is not None


# ============================================================================
# 消息历史测试
# ============================================================================

@pytest.mark.asyncio
async def test_message_history_update(basic_config):
    """测试消息历史更新"""
    agent = Agent(basic_config)
    
    # 执行第一次
    await agent.execute("First message")
    history1 = agent.get_history()
    assert len(history1) == 2  # user + assistant
    
    # 执行第二次
    await agent.execute("Second message")
    history2 = agent.get_history()
    assert len(history2) == 4  # 累计 4 条消息
    
    # 验证消息角色
    assert history2[0].role == MessageRole.USER
    assert history2[1].role == MessageRole.ASSISTANT


@pytest.mark.asyncio
async def test_message_history_clear(basic_config):
    """测试清空消息历史"""
    agent = Agent(basic_config)
    
    await agent.execute("Test message")
    assert len(agent.get_history()) > 0
    
    agent.clear_history()
    assert len(agent.get_history()) == 0


@pytest.mark.asyncio
async def test_message_history_trimming(basic_config):
    """测试消息历史修剪"""
    agent = Agent(basic_config)
    
    # 执行多次以积累历史
    for i in range(15):
        await agent.execute(f"Message {i}")
    
    history = agent.get_history()
    # 默认修剪到 20 条消息（10 轮对话 = 20 条消息）
    assert len(history) <= 20


# ============================================================================
# 执行上下文测试
# ============================================================================

@pytest.mark.asyncio
async def test_execution_context_creation(basic_config):
    """测试执行上下文创建"""
    agent = Agent(basic_config)
    
    context = ExecutionContext(
        session_id="test-session",
        metadata={"key": "value"}
    )
    
    result = await agent.execute("Hello", context=context)
    
    assert result.session_id == "test-session"


@pytest.mark.asyncio
async def test_execution_context_tools_merge(basic_config):
    """测试执行上下文工具合并"""
    agent = Agent(basic_config)
    agent.register_tool(create_calculator_tool())
    
    extra_tool = create_weather_tool()
    context = ExecutionContext(tools=[extra_tool])
    
    result = await agent.execute("Hello", context=context)
    
    assert result.output is not None


# ============================================================================
# 流式执行测试
# ============================================================================

@pytest.mark.asyncio
async def test_stream_execution(basic_config):
    """测试流式执行"""
    agent = Agent(basic_config)
    
    chunks = []
    async for chunk in agent.stream("Hello"):
        chunks.append(chunk)
    
    # 应该收到多个 chunks
    assert len(chunks) > 0
    assert agent.status == AgentStatus.IDLE


# ============================================================================
# 错误处理测试
# ============================================================================

@pytest.mark.asyncio
async def test_tool_execution_error(basic_config):
    """测试工具执行错误处理"""
    agent = Agent(basic_config)
    agent.register_tool(create_failing_tool())
    
    result = await agent.execute("Use failing tool")
    
    # 即使工具失败，也应该返回结果
    assert result.output is not None
    assert agent.status == AgentStatus.IDLE


@pytest.mark.asyncio
async def test_nonexistent_tool_handling(basic_config):
    """测试不存在的工具处理"""
    agent = Agent(basic_config)
    
    # 尝试获取不存在的工具
    tool = agent.get_tool("nonexistent")
    assert tool is None


# ============================================================================
# 集成测试
# ============================================================================

@pytest.mark.asyncio
async def test_full_react_workflow():
    """测试完整 ReAct 工作流"""
    config = AgentConfig(
        id="integration-agent",
        name="Integration Agent",
        model=ModelConfig(
            provider="openai",
            model="gpt-4",
            api_key="test-key"
        ),
        system_prompt="You are a helpful assistant.",
        max_iterations=10,
        tools=[
            create_calculator_tool(),
            create_search_tool(),
            create_weather_tool()
        ]
    )
    
    agent = Agent(config)
    progress_logs: List[str] = []
    
    async def on_progress(text: str):
        progress_logs.append(text)
    
    # 执行复杂查询
    result = await agent.execute(
        "Calculate 2+2 and search for Python",
        on_progress=on_progress
    )
    
    # 验证结果
    assert result.output is not None
    assert result.agent_id == "integration-agent"
    assert result.metadata.iterations >= 1
    assert result.duration >= 0
    assert agent.status == AgentStatus.IDLE
    
    # 验证消息历史
    history = agent.get_history()
    assert len(history) >= 2  # 至少 user + assistant


@pytest.mark.asyncio
async def test_concurrent_executions(basic_config):
    """测试并发执行"""
    agent = Agent(basic_config)
    
    # 并发执行多个任务
    tasks = [
        agent.execute(f"Task {i}")
        for i in range(3)
    ]
    
    results = await asyncio.gather(*tasks)
    
    # 所有任务都应该完成
    assert len(results) == 3
    for result in results:
        assert result.output is not None


# ============================================================================
# 边界条件测试
# ============================================================================

@pytest.mark.asyncio
async def test_empty_input(basic_config):
    """测试空输入"""
    agent = Agent(basic_config)
    
    result = await agent.execute("")
    
    assert result.output is not None


@pytest.mark.asyncio
async def test_long_input(basic_config):
    """测试长输入"""
    agent = Agent(basic_config)
    
    long_text = "Hello " * 1000
    result = await agent.execute(long_text)
    
    assert result.output is not None


@pytest.mark.asyncio
async def test_special_characters_input(basic_config):
    """测试特殊字符输入"""
    agent = Agent(basic_config)
    
    special_text = "Hello! @#$%^&*()_+ {}[]|\\:;\"'<>,.?/~`"
    result = await agent.execute(special_text)
    
    assert result.output is not None


@pytest.mark.asyncio
async def test_unicode_input(basic_config):
    """测试 Unicode 输入"""
    agent = Agent(basic_config)
    
    unicode_text = "你好世界 🌍 ñáéíóú 日本語"
    result = await agent.execute(unicode_text)
    
    assert result.output is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])