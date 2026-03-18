"""
测试技能模块
"""

import pytest
from unittest.mock import Mock

from nanosdk.skill import SkillManager, create_skill, SkillInitializationError
from nanosdk.types import Skill, Tool, ToolParameterSchema


class TestSkillManager:
    """测试技能管理器"""
    
    @pytest.fixture
    def manager(self):
        return SkillManager()
    
    def test_register_skill(self, manager):
        skill = Skill(
            name="test_skill",
            description="Test skill",
            version="1.0.0",
            tools=[],
        )
        
        manager.register(skill)
        assert manager.get("test_skill") == skill
    
    def test_register_with_initialize(self, manager):
        initialize_mock = Mock()
        
        skill = Skill(
            name="test_skill",
            description="Test skill",
            version="1.0.0",
            tools=[],
            initialize=initialize_mock,
        )
        
        manager.register(skill, context={"key": "value"})
        
        initialize_mock.assert_called_once_with({"key": "value"})
        assert manager._initialized["test_skill"] is True
    
    def test_register_initialize_error(self, manager):
        def bad_initialize(ctx):
            raise ValueError("Init failed")
        
        skill = Skill(
            name="test_skill",
            description="Test skill",
            version="1.0.0",
            tools=[],
            initialize=bad_initialize,
        )
        
        with pytest.raises(SkillInitializationError):
            manager.register(skill)
    
    def test_unregister_skill(self, manager):
        skill = Skill(
            name="test_skill",
            description="Test skill",
            version="1.0.0",
            tools=[],
        )
        
        manager.register(skill)
        manager.unregister("test_skill")
        
        assert manager.get("test_skill") is None
    
    def test_list_skills(self, manager):
        skill1 = Skill(name="skill1", description="Skill 1", version="1.0.0", tools=[])
        skill2 = Skill(name="skill2", description="Skill 2", version="1.0.0", tools=[])
        
        manager.register(skill1)
        manager.register(skill2)
        
        skills = manager.list()
        assert len(skills) == 2
    
    def test_get_all_tools(self, manager):
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
        
        skill1 = Skill(name="s1", description="S1", version="1.0.0", tools=[tool1])
        skill2 = Skill(name="s2", description="S2", version="1.0.0", tools=[tool2])
        
        manager.register(skill1)
        manager.register(skill2)
        
        tools = manager.get_all_tools()
        assert len(tools) == 2
        assert tool1 in tools
        assert tool2 in tools
    
    def test_get_tool(self, manager):
        def execute(args, ctx):
            return None
        
        tool = Tool(
            name="my_tool",
            description="My tool",
            parameters=ToolParameterSchema(),
            execute=execute,
        )
        
        skill = Skill(name="s1", description="S1", version="1.0.0", tools=[tool])
        manager.register(skill)
        
        found = manager.get_tool("my_tool")
        assert found == tool
    
    def test_get_tool_not_found(self, manager):
        assert manager.get_tool("nonexistent") is None
    
    def test_get_prompt(self, manager):
        skill = Skill(
            name="s1",
            description="S1",
            version="1.0.0",
            tools=[],
            prompts={"system": "You are helpful"},
        )
        manager.register(skill)
        
        prompt = manager.get_prompt("s1", "system")
        assert prompt == "You are helpful"
    
    def test_get_prompt_not_found(self, manager):
        skill = Skill(name="s1", description="S1", version="1.0.0", tools=[])
        manager.register(skill)
        
        assert manager.get_prompt("s1", "nonexistent") is None
        assert manager.get_prompt("nonexistent", "system") is None
    
    def test_clear(self, manager):
        skill = Skill(name="s1", description="S1", version="1.0.0", tools=[])
        manager.register(skill)
        manager.clear()
        
        assert manager.get("s1") is None
        assert len(manager.list()) == 0
    
    def test_to_dict(self, manager):
        skill = Skill(
            name="test_skill",
            description="Test skill",
            version="1.0.0",
            tools=[],
            prompts={"system": "Prompt"},
        )
        manager.register(skill)
        
        data = manager.to_dict()
        assert "test_skill" in data
        assert data["test_skill"]["version"] == "1.0.0"


class TestCreateSkill:
    """测试创建技能函数"""
    
    def test_create_skill(self):
        skill = create_skill(
            name="weather",
            description="Get weather info",
            version="1.0.0",
        )
        
        assert skill.name == "weather"
        assert skill.description == "Get weather info"
        assert skill.version == "1.0.0"
        assert skill.tools == []
    
    def test_create_skill_with_tools(self):
        def execute(args, ctx):
            return None
        
        tool = Tool(
            name="get_weather",
            description="Get weather",
            parameters=ToolParameterSchema(),
            execute=execute,
        )
        
        skill = create_skill(
            name="weather",
            description="Weather skill",
            tools=[tool],
        )
        
        assert len(skill.tools) == 1
        assert skill.tools[0].name == "get_weather"
