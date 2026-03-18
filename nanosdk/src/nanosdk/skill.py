"""
技能系统模块

支持模块化技能管理，包括工具、提示和初始化逻辑
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .types import Skill, Tool


@dataclass
class SkillManager:
    """
    技能管理器
    
    管理技能的注册、注销和工具聚合
    """
    
    _skills: Dict[str, Skill] = field(default_factory=dict)
    _initialized: Dict[str, bool] = field(default_factory=dict)
    
    def register(self, skill: Skill, context: Optional[Dict[str, Any]] = None) -> None:
        """
        注册技能
        
        Args:
            skill: 技能对象
            context: 初始化上下文
        """
        # 执行初始化
        if skill.initialize and not self._initialized.get(skill.name, False):
            try:
                skill.initialize(context or {})
                self._initialized[skill.name] = True
            except Exception as e:
                raise SkillInitializationError(f"Failed to initialize skill {skill.name}: {e}")
        
        self._skills[skill.name] = skill
    
    def unregister(self, name: str) -> None:
        """
        注销技能
        
        Args:
            name: 技能名称
        """
        if name in self._skills:
            del self._skills[name]
            self._initialized.pop(name, None)
    
    def get(self, name: str) -> Optional[Skill]:
        """
        获取技能
        
        Args:
            name: 技能名称
            
        Returns:
            Optional[Skill]: 技能对象
        """
        return self._skills.get(name)
    
    def list(self) -> List[Skill]:
        """
        列出所有技能
        
        Returns:
            List[Skill]: 技能列表
        """
        return list(self._skills.values())
    
    def get_all_tools(self) -> List[Tool]:
        """
        获取所有技能的工具
        
        Returns:
            List[Tool]: 工具列表
        """
        tools = []
        for skill in self._skills.values():
            tools.extend(skill.tools)
        return tools
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """
        获取指定名称的工具
        
        Args:
            name: 工具名称
            
        Returns:
            Optional[Tool]: 工具对象
        """
        for skill in self._skills.values():
            for tool in skill.tools:
                if tool.name == name:
                    return tool
        return None
    
    def get_prompt(self, skill_name: str, prompt_name: str) -> Optional[str]:
        """
        获取技能的提示
        
        Args:
            skill_name: 技能名称
            prompt_name: 提示名称
            
        Returns:
            Optional[str]: 提示内容
        """
        skill = self._skills.get(skill_name)
        if skill and skill.prompts:
            return skill.prompts.get(prompt_name)
        return None
    
    def clear(self) -> None:
        """清空所有技能"""
        self._skills.clear()
        self._initialized.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            Dict[str, Any]: 技能信息字典
        """
        return {
            name: {
                "name": skill.name,
                "description": skill.description,
                "version": skill.version,
                "tools": [tool.name for tool in skill.tools],
                "prompts": list(skill.prompts.keys()) if skill.prompts else [],
            }
            for name, skill in self._skills.items()
        }


class SkillInitializationError(Exception):
    """技能初始化错误"""
    pass


def create_skill(
    name: str,
    description: str,
    version: str = "1.0.0",
    tools: Optional[List[Tool]] = None,
    prompts: Optional[Dict[str, str]] = None,
    initialize: Optional[Callable[[Dict[str, Any]], None]] = None
) -> Skill:
    """
    创建技能
    
    Args:
        name: 技能名称
        description: 技能描述
        version: 版本号
        tools: 工具列表
        prompts: 提示字典
        initialize: 初始化函数
        
    Returns:
        Skill: 技能对象
    """
    return Skill(
        name=name,
        description=description,
        version=version,
        tools=tools or [],
        prompts=prompts,
        initialize=initialize
    )
