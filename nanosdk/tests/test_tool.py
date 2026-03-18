"""
测试工具模块
"""

import pytest
from unittest.mock import Mock

from nanosdk.tool import ToolRegistry, create_tool
from nanosdk.types import Tool, ToolParameterSchema, ToolContext, ToolResult


class TestToolRegistry:
    """测试工具注册表"""
    
    def test_register_tool(self):
        registry = ToolRegistry()
        
        def execute(args, ctx):
            return "result"
        
        tool = Tool(
            name="test",
            description="Test tool",
            parameters=ToolParameterSchema(),
            execute=execute,
        )
        
        registry.register(tool)
        assert registry.get("test") == tool
    
    def test_unregister_tool(self):
        registry = ToolRegistry()
        
        def execute(args, ctx):
            return None
        
        tool = Tool(
            name="test",
            description="Test tool",
            parameters=ToolParameterSchema(),
            execute=execute,
        )
        
        registry.register(tool)
        registry.unregister("test")
        assert registry.get("test") is None
    
    def test_list_tools(self):
        registry = ToolRegistry()
        
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
        
        registry.register(tool1)
        registry.register(tool2)
        
        tools = registry.list()
        assert len(tools) == 2
        assert tool1 in tools
        assert tool2 in tools
    
    def test_execute_tool_success(self):
        registry = ToolRegistry()
        
        def execute(args, ctx):
            return args["x"] + args["y"]
        
        tool = Tool(
            name="add",
            description="Add numbers",
            parameters=ToolParameterSchema(),
            execute=execute,
        )
        
        registry.register(tool)
        
        context = Mock(spec=ToolContext)
        result = registry.execute("add", {"x": 1, "y": 2}, context)
        
        assert result.result == 3
        assert result.error is None
        assert result.name == "add"
    
    def test_execute_tool_not_found(self):
        registry = ToolRegistry()
        context = Mock(spec=ToolContext)
        
        result = registry.execute("nonexistent", {}, context)
        
        assert result.result is None
        assert result.error == "Tool not found: nonexistent"
    
    def test_execute_tool_error(self):
        registry = ToolRegistry()
        
        def execute(args, ctx):
            raise ValueError("Invalid input")
        
        tool = Tool(
            name="error_tool",
            description="Error tool",
            parameters=ToolParameterSchema(),
            execute=execute,
        )
        
        registry.register(tool)
        
        context = Mock(spec=ToolContext)
        result = registry.execute("error_tool", {}, context)
        
        assert result.result is None
        assert "Invalid input" in result.error
    
    def test_clear(self):
        registry = ToolRegistry()
        
        def execute(args, ctx):
            return None
        
        tool = Tool(
            name="test",
            description="Test",
            parameters=ToolParameterSchema(),
            execute=execute,
        )
        
        registry.register(tool)
        registry.clear()
        
        assert registry.get("test") is None
        assert len(registry.list()) == 0
    
    def test_to_dict(self):
        registry = ToolRegistry()
        
        def execute(args, ctx):
            return None
        
        tool = Tool(
            name="test",
            description="Test tool",
            parameters=ToolParameterSchema(),
            execute=execute,
        )
        
        registry.register(tool)
        data = registry.to_dict()
        
        assert len(data) == 1
        assert data[0]["name"] == "test"


class TestCreateTool:
    """测试创建工具函数"""
    
    def test_create_tool(self):
        def execute(args, ctx):
            return args["value"]
        
        tool = create_tool(
            name="identity",
            description="Return value",
            parameters={
                "properties": {"value": {"type": "string"}},
                "required": ["value"],
            },
            execute=execute,
        )
        
        assert tool.name == "identity"
        assert tool.description == "Return value"
        assert "value" in tool.parameters.properties
