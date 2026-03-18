"""
子代理模块

支持创建和管理子代理，实现代理的层级结构和任务分发
"""

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .types import (
    AgentConfig,
    ExecutionContext,
    ExecutionResult,
    SubagentCall,
    SubagentConfig,
)
from .agent import Agent


@dataclass
class SubagentManager:
    """
    子代理管理器
    
    管理子代理的生命周期、调用和结果追踪
    """
    
    parent_agent: Agent
    _subagents: Dict[str, Agent] = field(default_factory=dict)
    _calls: List[SubagentCall] = field(default_factory=list)
    
    def create(
        self,
        config: SubagentConfig,
        context: Optional[ExecutionContext] = None
    ) -> Agent:
        """
        创建子代理
        
        Args:
            config: 子代理配置
            context: 执行上下文
            
        Returns:
            Agent: 创建的子代理
        """
        # 继承父代理的配置
        parent_config = self.parent_agent.config
        
        # 合并工具（从父代理配置和注册表）
        tools = []
        if config.inherit_tools:
            tools.extend(parent_config.tools)
            tools.extend(self.parent_agent.list_tools())
        if config.tools:
            tools.extend(config.tools)
        
        # 去重（按工具名称）
        seen = set()
        unique_tools = []
        for tool in tools:
            if tool.name not in seen:
                seen.add(tool.name)
                unique_tools.append(tool)
        tools = unique_tools
        
        # 合并技能
        skills = []
        if config.inherit_skills:
            skills.extend(parent_config.skills)
        if config.skills:
            skills.extend(config.skills)
        
        # 确定记忆配置
        memory = config.memory if not config.inherit_memory else parent_config.memory
        
        # 创建子代理配置
        subagent_config = AgentConfig(
            id=config.id or str(uuid.uuid4()),
            name=config.name,
            description=config.description,
            model=config.model or parent_config.model,
            tools=tools,
            skills=skills,
            memory=memory,
            system_prompt=config.system_prompt or parent_config.system_prompt,
            max_iterations=config.max_iterations or parent_config.max_iterations,
            temperature=config.temperature or parent_config.temperature,
        )
        
        # 创建子代理
        subagent = Agent(config=subagent_config)
        
        # 注册到管理器
        self._subagents[subagent.config.id] = subagent
        
        return subagent
    
    async def call(
        self,
        subagent_id: str,
        input: str,
        context: Optional[ExecutionContext] = None
    ) -> ExecutionResult:
        """
        调用子代理
        
        Args:
            subagent_id: 子代理 ID
            input: 输入内容
            context: 执行上下文
            
        Returns:
            ExecutionResult: 执行结果
            
        Raises:
            SubagentNotFoundError: 子代理不存在
        """
        subagent = self._subagents.get(subagent_id)
        if not subagent:
            raise SubagentNotFoundError(f"Subagent not found: {subagent_id}")
        
        # 创建执行上下文
        exec_context = context or ExecutionContext()
        exec_context.parent_execution_id = self.parent_agent._current_execution_id
        
        # 执行
        result = await subagent.execute(input, exec_context)
        
        # 记录调用
        call = SubagentCall(
            id=str(uuid.uuid4()),
            subagent_id=subagent_id,
            input=input,
            result=result,
            timestamp=datetime.now(),
        )
        self._calls.append(call)
        
        return result
    
    async def stream(
        self,
        subagent_id: str,
        input: str,
        context: Optional[ExecutionContext] = None
    ):
        """
        流式调用子代理
        
        Args:
            subagent_id: 子代理 ID
            input: 输入内容
            context: 执行上下文
            
        Yields:
            StreamChunk: 流式响应块
        """
        subagent = self._subagents.get(subagent_id)
        if not subagent:
            raise SubagentNotFoundError(f"Subagent not found: {subagent_id}")
        
        exec_context = context or ExecutionContext()
        exec_context.parent_execution_id = self.parent_agent._current_execution_id
        
        async for chunk in subagent.stream(input, exec_context):
            yield chunk
    
    def get(self, subagent_id: str) -> Optional[Agent]:
        """
        获取子代理
        
        Args:
            subagent_id: 子代理 ID
            
        Returns:
            Optional[Agent]: 子代理对象
        """
        return self._subagents.get(subagent_id)
    
    def list(self) -> List[Agent]:
        """
        列出所有子代理
        
        Returns:
            List[Agent]: 子代理列表
        """
        return list(self._subagents.values())
    
    def terminate(self, subagent_id: str) -> None:
        """
        终止子代理
        
        Args:
            subagent_id: 子代理 ID
        """
        if subagent_id in self._subagents:
            subagent = self._subagents[subagent_id]
            # 清理资源
            subagent.clear_history()
            del self._subagents[subagent_id]
    
    def get_calls(self, subagent_id: Optional[str] = None) -> List[SubagentCall]:
        """
        获取子代理调用记录
        
        Args:
            subagent_id: 子代理 ID，None 表示获取所有
            
        Returns:
            List[SubagentCall]: 调用记录列表
        """
        if subagent_id:
            return [call for call in self._calls if call.subagent_id == subagent_id]
        return self._calls.copy()
    
    def clear_calls(self) -> None:
        """清空调用记录"""
        self._calls.clear()
    
    def terminate_all(self) -> None:
        """终止所有子代理"""
        for subagent in self._subagents.values():
            subagent.clear_history()
        self._subagents.clear()


class SubagentNotFoundError(Exception):
    """子代理不存在错误"""
    pass


def create_subagent_config(
    name: str,
    parent_agent_id: str,
    model: Optional[Any] = None,
    tools: Optional[List[Any]] = None,
    skills: Optional[List[Any]] = None,
    inherit_tools: bool = True,
    inherit_skills: bool = True,
    inherit_memory: bool = False,
    **kwargs
) -> SubagentConfig:
    """
    创建子代理配置
    
    Args:
        name: 子代理名称
        parent_agent_id: 父代理 ID
        model: 模型配置
        tools: 工具列表
        skills: 技能列表
        inherit_tools: 是否继承父代理工具
        inherit_skills: 是否继承父代理技能
        inherit_memory: 是否继承父代理记忆
        **kwargs: 其他配置
        
    Returns:
        SubagentConfig: 子代理配置
    """
    return SubagentConfig(
        id=str(uuid.uuid4()),
        name=name,
        parent_agent_id=parent_agent_id,
        model=model,
        tools=tools or [],
        skills=skills or [],
        inherit_tools=inherit_tools,
        inherit_skills=inherit_skills,
        inherit_memory=inherit_memory,
        **kwargs
    )
