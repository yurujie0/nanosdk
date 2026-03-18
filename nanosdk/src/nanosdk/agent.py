"""
Agent 核心模块
"""

import asyncio
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .types import (
    AgentConfig,
    AgentStatus,
    ExecutionContext,
    ExecutionResult,
    ExecutionMetadata,
    Message,
    MessageRole,
    StreamChunk,
    Tool,
    ToolCall,
    ToolResult,
    TokenUsage,
    ModelConfig,
)
from .context import Context
from .tool import ToolRegistry
from .context import ContextManager


@dataclass
class Agent:
    """
    Agent 核心类
    
    负责管理 Agent 的生命周期、执行流程、工具调用和状态管理
    """
    
    config: AgentConfig
    status: AgentStatus = field(default=AgentStatus.IDLE)
    
    def __post_init__(self):
        """初始化 Agent"""
        self._tool_registry = ToolRegistry()
        self._context_manager = ContextManager()
        self._message_history: List[Message] = []
        self._current_execution_id: Optional[str] = None
        
        # 注册配置中的工具
        for tool in self.config.tools:
            self.register_tool(tool)
    
    # ============================================
    # 核心执行方法
    # ============================================
    
    async def execute(
        self,
        input: str,
        context: Optional[ExecutionContext] = None
    ) -> ExecutionResult:
        """
        执行 Agent
        
        Args:
            input: 用户输入
            context: 执行上下文
            
        Returns:
            ExecutionResult: 执行结果
        """
        self.status = AgentStatus.RUNNING
        start_time = datetime.now()
        execution_id = str(uuid.uuid4())
        session_id = context.session_id if context else str(uuid.uuid4())
        
        try:
            # 创建执行上下文
            exec_context = self._create_execution_context(context, session_id)
            
            # 构建消息列表
            messages = self._build_messages(input, exec_context)
            
            # 调用模型获取响应
            response = await self._call_model(messages)
            
            # 处理工具调用
            tool_calls, tool_results = await self._process_tools(response, exec_context)
            
            # 构建输出
            output = self._build_output(response, tool_results)
            
            # 更新消息历史
            self._update_message_history(input, output, tool_calls, tool_results)
            
            # 构建执行结果
            result = ExecutionResult(
                id=execution_id,
                agent_id=self.config.id,
                session_id=session_id,
                input=input,
                output=output,
                messages=messages,
                tool_calls=tool_calls,
                tool_results=tool_results,
                subagent_calls=[],  # TODO: 实现 subagent 调用
                metadata=ExecutionMetadata(
                    token_usage=TokenUsage(),  # TODO: 从模型响应获取
                    iterations=1,
                    model=self.config.model.model,
                    temperature=self.config.temperature,
                ),
                timestamp=datetime.now(),
                duration=(datetime.now() - start_time).total_seconds(),
            )
            
            self.status = AgentStatus.IDLE
            return result
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            raise AgentExecutionError(f"Execution failed: {str(e)}")
    
    async def stream(
        self,
        input: str,
        context: Optional[ExecutionContext] = None
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        流式执行 Agent
        
        Args:
            input: 用户输入
            context: 执行上下文
            
        Yields:
            StreamChunk: 流式响应块
        """
        self.status = AgentStatus.RUNNING
        
        try:
            session_id = context.session_id if context else str(uuid.uuid4())
            exec_context = self._create_execution_context(context, session_id)
            
            # 构建消息
            messages = self._build_messages(input, exec_context)
            
            # 流式调用模型
            async for chunk in self._call_model_stream(messages):
                yield chunk
            
            self.status = AgentStatus.IDLE
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            yield StreamChunk(
                type="error",
                error=str(e)
            )
    
    # ============================================
    # 工具管理
    # ============================================
    
    def register_tool(self, tool: Tool) -> None:
        """注册工具"""
        self._tool_registry.register(tool)
    
    def unregister_tool(self, name: str) -> None:
        """注销工具"""
        self._tool_registry.unregister(name)
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """获取工具"""
        return self._tool_registry.get(name)
    
    def list_tools(self) -> List[Tool]:
        """列出所有工具"""
        return self._tool_registry.list()
    
    # ============================================
    # 上下文管理
    # ============================================
    
    def create_context(
        self,
        context_id: str,
        parent_id: Optional[str] = None
    ) -> Context:
        """创建上下文"""
        return self._context_manager.create(context_id, parent_id)
    
    def get_context(self, context_id: str) -> Optional[Context]:
        """获取上下文"""
        return self._context_manager.get(context_id)
    
    def update_context(self, context_id: str, variables: Dict[str, Any]) -> None:
        """更新上下文"""
        self._context_manager.update(context_id, variables)
    
    # ============================================
    # 状态管理
    # ============================================
    
    def pause(self) -> None:
        """暂停 Agent"""
        if self.status == AgentStatus.RUNNING:
            self.status = AgentStatus.PAUSED
    
    def resume(self) -> None:
        """恢复 Agent"""
        if self.status == AgentStatus.PAUSED:
            self.status = AgentStatus.IDLE
    
    def clear_history(self) -> None:
        """清空消息历史"""
        self._message_history.clear()
    
    def get_history(self) -> List[Message]:
        """获取消息历史"""
        return self._message_history.copy()
    
    # ============================================
    # 内部方法
    # ============================================
    
    def _create_execution_context(
        self,
        context: Optional[ExecutionContext],
        session_id: str
    ) -> ExecutionContext:
        """创建执行上下文"""
        if context is None:
            return ExecutionContext(session_id=session_id)
        
        # 合并工具和技能
        tools = list(self.config.tools)
        if context.tools:
            tools.extend(context.tools)
        
        skills = list(self.config.skills)
        if context.skills:
            skills.extend(context.skills)
        
        return ExecutionContext(
            session_id=context.session_id or session_id,
            parent_execution_id=context.parent_execution_id,
            metadata=context.metadata,
            tools=tools,
            skills=skills,
        )
    
    def _build_messages(
        self,
        input: str,
        context: ExecutionContext
    ) -> List[Message]:
        """构建消息列表"""
        messages: List[Message] = []
        
        # 系统提示
        if self.config.system_prompt:
            messages.append(Message(
                id=str(uuid.uuid4()),
                role=MessageRole.SYSTEM,
                content=self._build_system_prompt(),
                timestamp=datetime.now(),
            ))
        
        # 历史消息
        messages.extend(self._message_history)
        
        # 用户输入
        messages.append(Message(
            id=str(uuid.uuid4()),
            role=MessageRole.USER,
            content=input,
            timestamp=datetime.now(),
        ))
        
        return messages
    
    def _build_system_prompt(self) -> str:
        """构建系统提示"""
        parts = []
        
        if self.config.system_prompt:
            parts.append(self.config.system_prompt)
        
        # 添加工具描述
        tools = self.list_tools()
        if tools:
            parts.append("\nAvailable tools:")
            for tool in tools:
                parts.append(f"- {tool.name}: {tool.description}")
        
        return "\n".join(parts)
    
    async def _call_model(self, messages: List[Message]) -> str:
        """
        调用模型
        
        TODO: 集成实际的 LLM API (OpenAI, Anthropic, etc.)
        """
        # 模拟模型调用
        await asyncio.sleep(0.1)
        
        last_message = messages[-1]
        return f"Response to: {last_message.content}"
    
    async def _call_model_stream(
        self,
        messages: List[Message]
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        流式调用模型
        
        TODO: 集成实际的 LLM API
        """
        # 模拟流式响应
        response = await self._call_model(messages)
        words = response.split()
        
        for word in words:
            await asyncio.sleep(0.05)
            yield StreamChunk(
                type="text",
                content=word + " "
            )
        
        yield StreamChunk(type="done")
    
    async def _process_tools(
        self,
        response: str,
        context: ExecutionContext
    ) -> tuple[List[ToolCall], List[ToolResult]]:
        """
        处理工具调用
        
        TODO: 实现实际的工具调用解析和执行
        """
        # 模拟工具调用检测
        tool_calls: List[ToolCall] = []
        tool_results: List[ToolResult] = []
        
        # 这里应该解析模型响应中的工具调用请求
        # 然后执行相应的工具
        
        return tool_calls, tool_results
    
    def _build_output(
        self,
        response: str,
        tool_results: List[ToolResult]
    ) -> str:
        """构建最终输出"""
        output = response
        
        # 如果有工具结果，可以附加到输出中
        if tool_results:
            tool_outputs = []
            for result in tool_results:
                if result.error:
                    tool_outputs.append(f"[Tool {result.name} failed: {result.error}]")
                else:
                    tool_outputs.append(f"[Tool {result.name} result: {result.result}]")
            
            output += "\n" + "\n".join(tool_outputs)
        
        return output
    
    def _update_message_history(
        self,
        input: str,
        output: str,
        tool_calls: List[ToolCall],
        tool_results: List[ToolResult]
    ) -> None:
        """更新消息历史"""
        # 添加用户消息
        self._message_history.append(Message(
            id=str(uuid.uuid4()),
            role=MessageRole.USER,
            content=input,
            timestamp=datetime.now(),
        ))
        
        # 添加助手消息
        self._message_history.append(Message(
            id=str(uuid.uuid4()),
            role=MessageRole.ASSISTANT,
            content=output,
            timestamp=datetime.now(),
            tool_calls=tool_calls if tool_calls else None,
            tool_results=tool_results if tool_results else None,
        ))
        
        # 限制历史长度
        self._trim_message_history()
    
    def _trim_message_history(self, max_messages: int = 20) -> None:
        """修剪消息历史"""
        if len(self._message_history) > max_messages:
            self._message_history = self._message_history[-max_messages:]


class AgentExecutionError(Exception):
    """Agent 执行错误"""
    pass
