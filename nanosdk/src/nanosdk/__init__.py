"""
NanoSDK - 轻量级 Python Agent SDK

支持工具调用、上下文管理、记忆、Agent Skills和Subagent
"""

__version__ = "0.1.0"
__author__ = "yurujie0"

from .agent import Agent
from .context import Context, ContextManager
from .memory import Memory, MemoryStore, InMemoryStore
from .skill import Skill, SkillManager
from .subagent import SubagentManager
from .tool import Tool, ToolParameterSchema
from .types import (
    Message,
    MessageRole,
    ToolCall,
    ToolResult,
    ExecutionResult,
    ExecutionContext,
    AgentConfig,
    AgentStatus,
    ModelConfig,
    MemoryConfig,
    ModelResponse,
    StreamChunk,
    ToolContext,
)

__all__ = [
    # Core
    "Agent",
    
    # Context
    "Context",
    "ContextManager",
    
    # Memory
    "Memory",
    "MemoryStore",
    "InMemoryStore",
    
    # Skills
    "Skill",
    "SkillManager",
    
    # Subagent
    "SubagentManager",
    
    # Tools
    "Tool",
    "ToolParameterSchema",
    "ToolContext",
    
    # Types
    "Message",
    "MessageRole",
    "ToolCall",
    "ToolResult",
    "ExecutionResult",
    "ExecutionContext",
    "AgentConfig",
    "AgentStatus",
    "ModelConfig",
    "MemoryConfig",
    "ModelResponse",
    "StreamChunk",
]
