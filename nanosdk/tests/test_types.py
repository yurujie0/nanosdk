"""
测试类型定义模块
"""

import pytest
from datetime import datetime
from dataclasses import asdict

from nanosdk.types import (
    MessageRole,
    AgentStatus,
    Message,
    ToolCall,
    ToolResult,
    ToolParameterSchema,
    Tool,
    ModelConfig,
    MemoryConfig,
    AgentConfig,
    ExecutionContext,
    TokenUsage,
    ExecutionMetadata,
)


class TestMessageRole:
    """测试消息角色枚举"""
    
    def test_message_role_values(self):
        assert MessageRole.SYSTEM == "system"
        assert MessageRole.USER == "user"
        assert MessageRole.ASSISTANT == "assistant"
        assert MessageRole.TOOL == "tool"


class TestAgentStatus:
    """测试 Agent 状态枚举"""
    
    def test_agent_status_values(self):
        assert AgentStatus.IDLE == "idle"
        assert AgentStatus.RUNNING == "running"
        assert AgentStatus.PAUSED == "paused"
        assert AgentStatus.ERROR == "error"


class TestMessage:
    """测试消息类"""
    
    def test_message_creation(self):
        msg = Message(
            id="msg-1",
            role=MessageRole.USER,
            content="Hello",
        )
        assert msg.id == "msg-1"
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello"
        assert isinstance(msg.timestamp, datetime)
    
    def test_message_with_tool_calls(self):
        tool_call = ToolCall(id="tc-1", name="calculator", arguments={"x": 1})
        msg = Message(
            id="msg-1",
            role=MessageRole.ASSISTANT,
            content="Result",
            tool_calls=[tool_call],
        )
        assert len(msg.tool_calls) == 1
        assert msg.tool_calls[0].name == "calculator"


class TestToolParameterSchema:
    """测试工具参数模式"""
    
    def test_default_values(self):
        schema = ToolParameterSchema()
        assert schema.type == "object"
        assert schema.properties == {}
        assert schema.required == []
    
    def test_to_dict(self):
        schema = ToolParameterSchema(
            properties={"name": {"type": "string"}},
            required=["name"],
        )
        data = schema.to_dict()
        assert data["type"] == "object"
        assert data["properties"] == {"name": {"type": "string"}}
        assert data["required"] == ["name"]


class TestTool:
    """测试工具类"""
    
    def test_tool_creation(self):
        def execute(args, ctx):
            return args["x"] + args["y"]
        
        tool = Tool(
            name="add",
            description="Add two numbers",
            parameters=ToolParameterSchema(
                properties={
                    "x": {"type": "number"},
                    "y": {"type": "number"},
                },
                required=["x", "y"],
            ),
            execute=execute,
        )
        assert tool.name == "add"
        assert tool.description == "Add two numbers"
    
    def test_tool_to_dict(self):
        def execute(args, ctx):
            return None
        
        tool = Tool(
            name="test",
            description="Test tool",
            parameters=ToolParameterSchema(),
            execute=execute,
        )
        data = tool.to_dict()
        assert data["name"] == "test"
        assert data["description"] == "Test tool"
        assert "parameters" in data


class TestModelConfig:
    """测试模型配置"""
    
    def test_default_values(self):
        config = ModelConfig(provider="openai", model="gpt-4")
        assert config.provider == "openai"
        assert config.model == "gpt-4"
        assert config.temperature == 0.7
        assert config.api_key is None
    
    def test_to_dict(self):
        config = ModelConfig(
            provider="openai",
            model="gpt-4",
            api_key="sk-xxx",
            temperature=0.5,
        )
        data = config.to_dict()
        assert data["provider"] == "openai"
        assert data["model"] == "gpt-4"
        assert data["api_key"] == "sk-xxx"
        assert data["temperature"] == 0.5


class TestAgentConfig:
    """测试 Agent 配置"""
    
    def test_default_values(self):
        config = AgentConfig(id="agent-1", name="Test Agent")
        assert config.id == "agent-1"
        assert config.name == "Test Agent"
        assert config.tools == []
        assert config.skills == []
        assert config.max_iterations == 10
        assert config.temperature == 0.7
    
    def test_with_tools(self):
        def execute(args, ctx):
            return None
        
        tool = Tool(
            name="test",
            description="Test",
            parameters=ToolParameterSchema(),
            execute=execute,
        )
        config = AgentConfig(
            id="agent-1",
            name="Test Agent",
            tools=[tool],
        )
        assert len(config.tools) == 1
        assert config.tools[0].name == "test"


class TestExecutionContext:
    """测试执行上下文"""
    
    def test_default_values(self):
        ctx = ExecutionContext()
        assert ctx.session_id is None
        assert ctx.parent_execution_id is None
        assert ctx.metadata == {}
        assert ctx.tools is None
        assert ctx.skills is None
    
    def test_with_metadata(self):
        ctx = ExecutionContext(metadata={"key": "value"})
        assert ctx.metadata["key"] == "value"


class TestTokenUsage:
    """测试 Token 使用统计"""
    
    def test_default_values(self):
        usage = TokenUsage()
        assert usage.prompt == 0
        assert usage.completion == 0
        assert usage.total == 0


class TestExecutionMetadata:
    """测试执行元数据"""
    
    def test_default_values(self):
        meta = ExecutionMetadata()
        assert meta.iterations == 0
        assert meta.model == ""
        assert meta.temperature == 0.7
        assert isinstance(meta.token_usage, TokenUsage)
