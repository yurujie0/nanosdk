"""
测试子代理模块
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from nanosdk.subagent import SubagentManager, SubagentNotFoundError, create_subagent_config
from nanosdk.agent import Agent
from nanosdk.types import (
    AgentConfig,
    ModelConfig,
    SubagentConfig,
    ExecutionContext,
)


class TestSubagentManager:
    """测试子代理管理器"""
    
    @pytest.fixture
    def parent_agent(self):
        config = AgentConfig(
            id="parent",
            name="Parent Agent",
            model=ModelConfig(provider="openai", model="gpt-4"),
        )
        return Agent(config=config)
    
    @pytest.fixture
    def manager(self, parent_agent):
        return SubagentManager(parent_agent=parent_agent)
    
    def test_create_subagent(self, manager, parent_agent):
        config = SubagentConfig(
            id="child",
            name="Child Agent",
            parent_agent_id="parent",
        )
        
        subagent = manager.create(config)
        
        assert subagent is not None
        assert subagent.config.name == "Child Agent"
        assert manager.get("child") == subagent
    
    def test_create_with_inheritance(self, manager, parent_agent):
        def execute(args, ctx):
            return None
        
        from nanosdk.types import Tool, ToolParameterSchema
        
        tool = Tool(
            name="parent_tool",
            description="Parent tool",
            parameters=ToolParameterSchema(),
            execute=execute,
        )
        parent_agent.register_tool(tool)
        
        config = SubagentConfig(
            id="child",
            name="Child Agent",
            parent_agent_id="parent",
            inherit_tools=True,
        )
        
        subagent = manager.create(config)
        
        # Should inherit parent's tools
        assert len(subagent.list_tools()) >= 1
    
    @pytest.mark.asyncio
    async def test_call_subagent(self, manager):
        config = SubagentConfig(
            id="worker",
            name="Worker",
            parent_agent_id="parent",
        )
        
        # Create the subagent
        manager.create(config)
        
        # Mock the execute method
        subagent = manager.get("worker")
        subagent.execute = AsyncMock(return_value=Mock(
            output="Task completed",
            id="result-1",
        ))
        
        result = await manager.call("worker", "Do something")
        
        assert result.output == "Task completed"
        assert len(manager.get_calls("worker")) == 1
    
    @pytest.mark.asyncio
    async def test_call_nonexistent_subagent(self, manager):
        with pytest.raises(SubagentNotFoundError):
            await manager.call("nonexistent", "Do something")
    
    def test_list_subagents(self, manager):
        config1 = SubagentConfig(id="s1", name="S1", parent_agent_id="parent")
        config2 = SubagentConfig(id="s2", name="S2", parent_agent_id="parent")
        
        manager.create(config1)
        manager.create(config2)
        
        subagents = manager.list()
        assert len(subagents) == 2
    
    def test_terminate_subagent(self, manager):
        config = SubagentConfig(id="temp", name="Temp", parent_agent_id="parent")
        manager.create(config)
        
        manager.terminate("temp")
        
        assert manager.get("temp") is None
    
    def test_get_calls(self, manager):
        config = SubagentConfig(id="worker", name="Worker", parent_agent_id="parent")
        manager.create(config)
        
        # Manually add a call record
        from nanosdk.types import SubagentCall
        call = SubagentCall(
            id="call-1",
            subagent_id="worker",
            input="Test",
            result=Mock(),
            timestamp=datetime.now(),
        )
        manager._calls.append(call)
        
        calls = manager.get_calls("worker")
        assert len(calls) == 1
        assert calls[0].subagent_id == "worker"
    
    def test_get_all_calls(self, manager):
        config1 = SubagentConfig(id="s1", name="S1", parent_agent_id="parent")
        config2 = SubagentConfig(id="s2", name="S2", parent_agent_id="parent")
        
        manager.create(config1)
        manager.create(config2)
        
        from nanosdk.types import SubagentCall
        manager._calls.append(SubagentCall(
            id="c1", subagent_id="s1", input="Test", result=Mock(), timestamp=datetime.now()
        ))
        manager._calls.append(SubagentCall(
            id="c2", subagent_id="s2", input="Test", result=Mock(), timestamp=datetime.now()
        ))
        
        calls = manager.get_calls()
        assert len(calls) == 2
    
    def test_clear_calls(self, manager):
        from nanosdk.types import SubagentCall
        manager._calls.append(SubagentCall(
            id="c1", subagent_id="s1", input="Test", result=Mock(), timestamp=datetime.now()
        ))
        
        manager.clear_calls()
        assert len(manager._calls) == 0
    
    def test_terminate_all(self, manager):
        config1 = SubagentConfig(id="s1", name="S1", parent_agent_id="parent")
        config2 = SubagentConfig(id="s2", name="S2", parent_agent_id="parent")
        
        manager.create(config1)
        manager.create(config2)
        
        manager.terminate_all()
        
        assert len(manager.list()) == 0


class TestSubagentNotFoundError:
    """测试子代理不存在错误"""
    
    def test_error_message(self):
        error = SubagentNotFoundError("Agent not found: test")
        assert str(error) == "Agent not found: test"


class TestCreateSubagentConfig:
    """测试创建子代理配置函数"""
    
    def test_create_config(self):
        config = create_subagent_config(
            name="Worker",
            parent_agent_id="parent-1",
        )
        
        assert config.name == "Worker"
        assert config.parent_agent_id == "parent-1"
        assert config.inherit_tools is True
        assert config.inherit_skills is True
        assert config.inherit_memory is False
    
    def test_create_with_custom_model(self):
        model = ModelConfig(provider="anthropic", model="claude-3")
        config = create_subagent_config(
            name="Worker",
            parent_agent_id="parent-1",
            model=model,
        )
        
        assert config.model == model
