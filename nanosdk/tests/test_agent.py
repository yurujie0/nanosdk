"""
测试 Agent 模块
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime

from nanosdk.agent import Agent, AgentExecutionError
from nanosdk.types import (
    AgentConfig,
    ModelConfig,
    Tool,
    ToolParameterSchema,
    MessageRole,
)


class TestAgent:
    """测试 Agent 类"""
    
    @pytest.fixture
    def config(self):
        return AgentConfig(
            id="test-agent",
            name="Test Agent",
            model=ModelConfig(provider="openai", model="gpt-4"),
            system_prompt="You are a helpful assistant.",
        )
    
    @pytest.fixture
    def agent(self, config):
        return Agent(config=config)
    
    def test_agent_creation(self, agent, config):
        assert agent.config == config
        assert agent.status.value == "idle"
    
    def test_register_tool(self, agent):
        def execute(args, ctx):
            return "result"
        
        tool = Tool(
            name="test_tool",
            description="Test tool",
            parameters=ToolParameterSchema(),
            execute=execute,
        )
        
        agent.register_tool(tool)
        assert agent.get_tool("test_tool") == tool
    
    def test_unregister_tool(self, agent):
        def execute(args, ctx):
            return None
        
        tool = Tool(
            name="test_tool",
            description="Test tool",
            parameters=ToolParameterSchema(),
            execute=execute,
        )
        
        agent.register_tool(tool)
        agent.unregister_tool("test_tool")
        assert agent.get_tool("test_tool") is None
    
    def test_list_tools(self, agent):
        def execute(args, ctx):
            return None
        
        tool1 = Tool(
            name="tool1",
            description="Tool 1",
            parameters=ToolParameterSchema(),
            execute=execute,
        )
        tool2 = Tool(
            name="tool2",
            description="Tool 2",
            parameters=ToolParameterSchema(),
            execute=execute,
        )
        
        agent.register_tool(tool1)
        agent.register_tool(tool2)
        
        tools = agent.list_tools()
        assert len(tools) == 2
    
    def test_create_context(self, agent):
        ctx = agent.create_context("ctx-1")
        assert ctx is not None
        assert agent.get_context("ctx-1") == ctx
    
    def test_update_context(self, agent):
        agent.create_context("ctx-1")
        agent.update_context("ctx-1", {"key": "value"})
        
        ctx = agent.get_context("ctx-1")
        assert ctx.get("key") == "value"
    
    def test_pause_resume(self, agent):
        # Set status to running first
        agent.status = Mock()
        agent.status = Mock()
        agent.status.value = "running"
        
        agent.pause()
        # Status should be paused
        
        agent.resume()
        # Status should be idle
    
    def test_clear_history(self, agent):
        # Add some history
        agent._message_history.append(Mock())
        agent.clear_history()
        assert len(agent._message_history) == 0
    
    def test_get_history(self, agent):
        from nanosdk.types import Message
        
        msg = Message(
            id="msg-1",
            role=MessageRole.USER,
            content="Hello",
        )
        agent._message_history.append(msg)
        
        history = agent.get_history()
        assert len(history) == 1
        assert history[0].content == "Hello"
    
    @pytest.mark.asyncio
    async def test_execute(self, agent):
        # This is a basic test - the actual model call is mocked
        result = await agent.execute("Hello")
        
        assert result.input == "Hello"
        assert result.agent_id == "test-agent"
        assert result.output is not None
        assert result.duration >= 0
    
    @pytest.mark.asyncio
    async def test_stream(self, agent):
        chunks = []
        async for chunk in agent.stream("Hello"):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        # Last chunk should be done
        assert chunks[-1].type == "done"
    
    def test_build_system_prompt_with_tools(self, agent):
        def execute(args, ctx):
            return None
        
        tool = Tool(
            name="calculator",
            description="Calculate expressions",
            parameters=ToolParameterSchema(),
            execute=execute,
        )
        
        agent.register_tool(tool)
        prompt = agent._build_system_prompt()
        
        assert "You are a helpful assistant" in prompt
        assert "calculator" in prompt
        assert "Calculate expressions" in prompt


class TestAgentExecutionError:
    """测试 Agent 执行错误"""
    
    def test_error_message(self):
        error = AgentExecutionError("Test error")
        assert str(error) == "Test error"
