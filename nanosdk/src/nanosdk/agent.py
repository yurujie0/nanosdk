"""
Agent 核心模块 - ReAct 范式实现

参考 HKUDS/nanobot 的 ReAct 实现
"""

import asyncio
import json
import uuid
import re
from typing import Any, AsyncGenerator, Dict, List, Optional, Callable, Awaitable
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
    ModelResponse,
)
from .context import Context
from .tool import ToolRegistry
from .context import ContextManager


@dataclass
class Agent:
    """
    Agent 核心类 - ReAct 范式实现
    
    负责管理 Agent 的生命周期、执行流程、工具调用和状态管理
    采用 ReAct (Reasoning + Acting) 范式：
    - Thought: LLM 推理/思考
    - Action: 执行工具调用
    - Observation: 观察工具执行结果
    - 循环直到任务完成
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
    # 核心执行方法 - ReAct 循环
    # ============================================
    
    async def execute(
        self,
        input: str,
        context: Optional[ExecutionContext] = None,
        on_progress: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> ExecutionResult:
        """
        执行 Agent - ReAct 范式
        
        Args:
            input: 用户输入
            context: 执行上下文
            on_progress: 进度回调函数
            
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
            
            # 构建初始消息列表
            messages = self._build_initial_messages(input, exec_context)
            
            # 运行 ReAct 循环
            final_content, all_tool_calls, all_tool_results, final_messages = await self._run_react_loop(
                messages=messages,
                max_iterations=self.config.max_iterations,
                on_progress=on_progress
            )
            
            # 更新消息历史
            self._update_message_history(input, final_content, all_tool_calls, all_tool_results)
            
            # 构建执行结果
            result = ExecutionResult(
                id=execution_id,
                agent_id=self.config.id,
                session_id=session_id,
                input=input,
                output=final_content or "I've completed processing but have no response to give.",
                messages=final_messages,
                tool_calls=all_tool_calls,
                tool_results=all_tool_results,
                subagent_calls=[],
                metadata=ExecutionMetadata(
                    token_usage=TokenUsage(),  # TODO: 从模型响应获取
                    iterations=len(all_tool_calls) + 1,
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
    
    async def _run_react_loop(
        self,
        messages: List[Message],
        max_iterations: int = 10,
        on_progress: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> tuple[Optional[str], List[ToolCall], List[ToolResult], List[Message]]:
        """
        运行 ReAct 循环
        
        ReAct 范式核心：
        1. 调用 LLM 获取响应（可能包含推理/思考内容）
        2. 如果响应包含工具调用（Action），执行工具
        3. 将工具结果（Observation）添加回消息历史
        4. 继续循环直到没有工具调用或达到最大迭代次数
        
        Args:
            messages: 初始消息列表
            max_iterations: 最大迭代次数
            on_progress: 进度回调
            
        Returns:
            (final_content, all_tool_calls, all_tool_results, final_messages)
        """
        iteration = 0
        final_content: Optional[str] = None
        all_tool_calls: List[ToolCall] = []
        all_tool_results: List[ToolResult] = []
        
        while iteration < max_iterations:
            iteration += 1
            
            # 获取工具定义
            tool_definitions = self._get_tool_definitions()
            
            # 调用模型
            response = await self._call_model_with_tools(messages, tool_definitions)
            
            if response.has_tool_calls and response.tool_calls:
                # Thought: 处理推理内容
                thought = self._strip_think(response.content)
                if thought and on_progress:
                    await on_progress(thought)
                
                # Action: 添加助手消息（包含 tool_calls）
                messages = self._add_assistant_message(
                    messages, 
                    content=response.content,
                    tool_calls=response.tool_calls,
                    reasoning_content=response.reasoning_content
                )
                
                # 执行每个工具调用
                for tool_call in response.tool_calls:
                    all_tool_calls.append(tool_call)
                    
                    # 执行工具
                    tool_result = await self._execute_tool(tool_call)
                    all_tool_results.append(tool_result)
                    
                    # Observation: 添加工具结果到消息历史
                    messages = self._add_tool_result_message(
                        messages, tool_call.id, tool_call.name, tool_result
                    )
            else:
                # 没有工具调用，任务完成
                clean_content = self._strip_think(response.content)
                messages = self._add_assistant_message(
                    messages, 
                    content=clean_content,
                    reasoning_content=response.reasoning_content
                )
                final_content = clean_content
                break
        
        # 如果达到最大迭代次数仍未完成
        if final_content is None and iteration >= max_iterations:
            final_content = (
                f"I reached the maximum number of tool call iterations ({max_iterations}) "
                "without completing the task. You can try breaking the task into smaller steps."
            )
        
        return final_content, all_tool_calls, all_tool_results, messages
    
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
            messages = self._build_initial_messages(input, exec_context)
            
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
    
    def _get_tool_definitions(self) -> List[Dict[str, Any]]:
        """获取工具定义列表（用于 LLM 调用）"""
        return [tool.to_dict() for tool in self.list_tools()]
    
    async def _execute_tool(self, tool_call: ToolCall) -> Any:
        """
        执行工具调用
        
        Args:
            tool_call: 工具调用信息
            
        Returns:
            工具执行结果
        """
        tool = self.get_tool(tool_call.name)
        if not tool:
            return f"Error: Tool '{tool_call.name}' not found"
        
        try:
            from .types import ToolContext
            tool_context = ToolContext(
                agent=self,
                session_id=str(uuid.uuid4()),  # TODO: 使用实际 session_id
                memory=None  # TODO: 集成记忆系统
            )
            result = tool.execute(tool_call.arguments, tool_context)
            
            # 如果结果是协程，等待执行完成
            if asyncio.iscoroutine(result):
                result = await result
                
            return result
        except Exception as e:
            return f"Error executing tool '{tool_call.name}': {str(e)}"
    
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
    
    def _build_initial_messages(
        self,
        input: str,
        context: ExecutionContext
    ) -> List[Message]:
        """构建初始消息列表"""
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
        
        # 添加 ReAct 指导
        parts.append("""
You are an AI assistant that can use tools to help users. Follow the ReAct pattern:
1. Think about what you need to do (Reasoning)
2. Use available tools if needed (Action)
3. Observe the results and continue if necessary (Observation)

Available tools:""")
        
        # 添加工具描述
        tools = self.list_tools()
        if tools:
            for tool in tools:
                parts.append(f"- {tool.name}: {tool.description}")
        
        return "\n".join(parts)
    
    async def _call_model_with_tools(
        self,
        messages: List[Message],
        tools: List[Dict[str, Any]]
    ) -> ModelResponse:
        """
        调用模型（支持工具调用）
        
        TODO: 集成实际的 LLM API (OpenAI, Anthropic, etc.)
        当前为模拟实现
        """
        await asyncio.sleep(0.1)
        
        # 模拟模型响应
        last_message = messages[-1]
        
        # 简单模拟：如果用户消息包含特定关键词，返回工具调用
        if "search" in last_message.content.lower() and tools:
            return ModelResponse(
                content="I'll search for that information.",
                tool_calls=[
                    ToolCall(
                        id=f"call_{uuid.uuid4().hex[:8]}",
                        name="web_search",
                        arguments={"query": last_message.content}
                    )
                ],
                has_tool_calls=True,
                finish_reason="tool_calls"
            )
        
        return ModelResponse(
            content=f"Response to: {last_message.content}",
            has_tool_calls=False,
            finish_reason="stop"
        )
    
    async def _call_model_stream(
        self,
        messages: List[Message]
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        流式调用模型
        
        TODO: 集成实际的 LLM API
        """
        # 模拟流式响应
        response_text = f"Response to: {messages[-1].content}"
        words = response_text.split()
        
        for word in words:
            await asyncio.sleep(0.05)
            yield StreamChunk(
                type="text",
                content=word + " "
            )
        
        yield StreamChunk(type="done")
    
    def _add_assistant_message(
        self,
        messages: List[Message],
        content: Optional[str] = None,
        tool_calls: Optional[List[ToolCall]] = None,
        reasoning_content: Optional[str] = None
    ) -> List[Message]:
        """添加助手消息到消息列表"""
        messages.append(Message(
            id=str(uuid.uuid4()),
            role=MessageRole.ASSISTANT,
            content=content,
            tool_calls=tool_calls,
            reasoning_content=reasoning_content,
            timestamp=datetime.now(),
        ))
        return messages
    
    def _add_tool_result_message(
        self,
        messages: List[Message],
        tool_call_id: str,
        tool_name: str,
        result: Any
    ) -> List[Message]:
        """添加工具结果消息到消息列表"""
        result_str = str(result) if result is not None else ""
        
        messages.append(Message(
            id=str(uuid.uuid4()),
            role=MessageRole.TOOL,
            content=result_str,
            timestamp=datetime.now(),
            metadata={
                "tool_call_id": tool_call_id,
                "tool_name": tool_name
            }
        ))
        return messages
    
    @staticmethod
    def _strip_think(text: Optional[str]) -> Optional[str]:
        """
        移除 <think>...</think> 或 <thinking>...</thinking> 块
        某些模型会在内容中嵌入推理块
        """
        if not text:
            return None
        # 移除 <think> 和 <thinking> 块
        text = re.sub(r"<think>[\s\S]*?</think>", "", text).strip()
        text = re.sub(r"<thinking>[\s\S]*?</thinking>", "", text).strip()
        return text or None
    
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
