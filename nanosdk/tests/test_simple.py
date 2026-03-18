"""
简单的 ReAct Agent 测试（无需 pytest）
"""

import asyncio
import sys
from typing import List

# 添加 src 到路径
sys.path.insert(0, "/home/admin/.openclaw/workspace/nanosdk-react/nanosdk/src")

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
# 测试工具
# ============================================================================

def create_calculator_tool() -> Tool:
    """创建计算器工具"""
    def execute(args: dict, ctx: ToolContext) -> str:
        expression = args.get("expression", "")
        try:
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
                    "description": "Math expression to evaluate"
                }
            },
            required=["expression"]
        ),
        execute=execute
    )


def create_search_tool() -> Tool:
    """创建搜索工具"""
    async def execute(args: dict, ctx: ToolContext) -> str:
        query = args.get("query", "")
        await asyncio.sleep(0.01)
        return f"Search results for: {query}"
    
    return Tool(
        name="search",
        description="Search for information",
        parameters=ToolParameterSchema(
            properties={
                "query": {"type": "string", "description": "Search query"}
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
        description="Get weather information",
        parameters=ToolParameterSchema(
            properties={
                "location": {"type": "string", "description": "City name"}
            },
            required=["location"]
        ),
        execute=execute
    )


# ============================================================================
# 测试函数
# ============================================================================

async def test_basic_initialization():
    """测试基础初始化"""
    print("\n[Test] Basic Initialization")
    
    config = AgentConfig(
        id="test-agent",
        name="Test Agent",
        model=ModelConfig(provider="openai", model="gpt-4", api_key="test"),
        max_iterations=5
    )
    
    agent = Agent(config)
    
    assert agent.config.id == "test-agent"
    assert agent.status == AgentStatus.IDLE
    assert len(agent.list_tools()) == 0
    
    print("  ✓ Agent initialized correctly")


async def test_tool_registration():
    """测试工具注册"""
    print("\n[Test] Tool Registration")
    
    config = AgentConfig(
        id="test-agent",
        name="Test Agent",
        model=ModelConfig(provider="openai", model="gpt-4", api_key="test"),
        max_iterations=5
    )
    
    agent = Agent(config)
    calculator = create_calculator_tool()
    
    # 注册
    agent.register_tool(calculator)
    assert len(agent.list_tools()) == 1
    assert agent.get_tool("calculator") is not None
    print("  ✓ Tool registered")
    
    # 注销
    agent.unregister_tool("calculator")
    assert len(agent.list_tools()) == 0
    print("  ✓ Tool unregistered")


async def test_react_execution_no_tools():
    """测试无工具的 ReAct 执行"""
    print("\n[Test] ReAct Execution (No Tools)")
    
    config = AgentConfig(
        id="test-agent",
        name="Test Agent",
        model=ModelConfig(provider="openai", model="gpt-4", api_key="test"),
        system_prompt="You are helpful.",
        max_iterations=5
    )
    
    agent = Agent(config)
    result = await agent.execute("Hello")
    
    assert result.output is not None
    assert len(result.tool_calls) == 0
    assert result.metadata.iterations == 1
    assert agent.status == AgentStatus.IDLE
    
    print(f"  ✓ Execution completed: {result.output[:50]}...")
    print(f"  ✓ Iterations: {result.metadata.iterations}")


async def test_react_execution_with_tools():
    """测试带工具的 ReAct 执行"""
    print("\n[Test] ReAct Execution (With Tools)")
    
    config = AgentConfig(
        id="test-agent",
        name="Test Agent",
        model=ModelConfig(provider="openai", model="gpt-4", api_key="test"),
        system_prompt="You are helpful.",
        max_iterations=5,
        tools=[create_calculator_tool(), create_search_tool()]
    )
    
    agent = Agent(config)
    result = await agent.execute("Calculate 2 + 2")
    
    assert result.output is not None
    assert result.metadata.iterations >= 1
    assert agent.status == AgentStatus.IDLE
    
    print(f"  ✓ Execution completed: {result.output[:50]}...")
    print(f"  ✓ Iterations: {result.metadata.iterations}")


async def test_progress_callback():
    """测试进度回调"""
    print("\n[Test] Progress Callback")
    
    config = AgentConfig(
        id="test-agent",
        name="Test Agent",
        model=ModelConfig(provider="openai", model="gpt-4", api_key="test"),
        max_iterations=5
    )
    
    agent = Agent(config)
    progress_logs: List[str] = []
    
    async def on_progress(text: str):
        progress_logs.append(text)
        print(f"    Progress: {text[:40]}...")
    
    result = await agent.execute("Hello", on_progress=on_progress)
    
    assert result.output is not None
    print(f"  ✓ Progress callbacks received: {len(progress_logs)}")


async def test_message_history():
    """测试消息历史"""
    print("\n[Test] Message History")
    
    config = AgentConfig(
        id="test-agent",
        name="Test Agent",
        model=ModelConfig(provider="openai", model="gpt-4", api_key="test"),
        max_iterations=5
    )
    
    agent = Agent(config)
    
    # 第一次执行
    await agent.execute("First message")
    history1 = agent.get_history()
    assert len(history1) == 2  # user + assistant
    print(f"  ✓ After 1st execution: {len(history1)} messages")
    
    # 第二次执行
    await agent.execute("Second message")
    history2 = agent.get_history()
    assert len(history2) == 4  # 累计 4 条
    print(f"  ✓ After 2nd execution: {len(history2)} messages")
    
    # 验证角色
    assert history2[0].role == MessageRole.USER
    assert history2[1].role == MessageRole.ASSISTANT
    print("  ✓ Message roles correct")
    
    # 清空历史
    agent.clear_history()
    assert len(agent.get_history()) == 0
    print("  ✓ History cleared")


async def test_execution_context():
    """测试执行上下文"""
    print("\n[Test] Execution Context")
    
    config = AgentConfig(
        id="test-agent",
        name="Test Agent",
        model=ModelConfig(provider="openai", model="gpt-4", api_key="test"),
        max_iterations=5
    )
    
    agent = Agent(config)
    
    context = ExecutionContext(
        session_id="test-session-123",
        metadata={"key": "value"}
    )
    
    result = await agent.execute("Hello", context=context)
    
    assert result.session_id == "test-session-123"
    print("  ✓ Session ID preserved")


async def test_stream_execution():
    """测试流式执行"""
    print("\n[Test] Stream Execution")
    
    config = AgentConfig(
        id="test-agent",
        name="Test Agent",
        model=ModelConfig(provider="openai", model="gpt-4", api_key="test"),
        max_iterations=5
    )
    
    agent = Agent(config)
    chunks = []
    
    async for chunk in agent.stream("Hello"):
        chunks.append(chunk)
    
    assert len(chunks) > 0
    assert agent.status == AgentStatus.IDLE
    
    print(f"  ✓ Stream received {len(chunks)} chunks")


async def test_full_workflow():
    """测试完整工作流"""
    print("\n[Test] Full Workflow")
    
    config = AgentConfig(
        id="workflow-agent",
        name="Workflow Agent",
        model=ModelConfig(provider="openai", model="gpt-4", api_key="test"),
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
    
    result = await agent.execute(
        "Calculate 2+2",
        on_progress=on_progress
    )
    
    assert result.output is not None
    assert result.agent_id == "workflow-agent"
    assert result.metadata.iterations >= 1
    
    print(f"  ✓ Output: {result.output[:50]}...")
    print(f"  ✓ Iterations: {result.metadata.iterations}")
    print(f"  ✓ Duration: {result.duration:.2f}s")


async def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("ReAct Agent Tests")
    print("=" * 60)
    
    tests = [
        test_basic_initialization,
        test_tool_registration,
        test_react_execution_no_tools,
        test_react_execution_with_tools,
        test_progress_callback,
        test_message_history,
        test_execution_context,
        test_stream_execution,
        test_full_workflow,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"  ✗ Failed: {e}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)