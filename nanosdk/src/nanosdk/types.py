"""
核心类型定义
"""

from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class MessageRole(str, Enum):
    """消息角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class AgentStatus(str, Enum):
    """Agent状态"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class Message:
    """消息"""
    id: str
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List["ToolCall"]] = None
    tool_results: Optional[List["ToolResult"]] = None


@dataclass
class ToolCall:
    """工具调用"""
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class ToolResult:
    """工具执行结果"""
    tool_call_id: str
    name: str
    result: Any
    error: Optional[str] = None


@dataclass
class ToolParameterSchema:
    """工具参数模式"""
    type: str = "object"
    properties: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    required: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "properties": self.properties,
            "required": self.required,
        }


@dataclass
class Tool:
    """工具定义"""
    name: str
    description: str
    parameters: ToolParameterSchema
    execute: Callable[[Dict[str, Any], "ToolContext"], Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters.to_dict(),
        }


@dataclass
class ToolContext:
    """工具执行上下文"""
    agent: "Agent"
    session_id: str
    memory: Optional["MemoryStore"] = None


@dataclass
class ModelConfig:
    """模型配置"""
    provider: str  # "openai", "anthropic", "custom"
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: float = 0.7
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "api_key": self.api_key,
            "base_url": self.base_url,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }


@dataclass
class MemoryConfig:
    """记忆配置"""
    type: str = "short-term"  # "short-term", "long-term", "hybrid"
    max_tokens: Optional[int] = None
    ttl: Optional[int] = None  # 毫秒


@dataclass
class AgentConfig:
    """Agent配置"""
    id: str
    name: str
    description: Optional[str] = None
    model: ModelConfig = field(default_factory=lambda: ModelConfig(provider="openai", model="gpt-4"))
    tools: List[Tool] = field(default_factory=list)
    skills: List["Skill"] = field(default_factory=list)
    memory: Optional[MemoryConfig] = None
    system_prompt: Optional[str] = None
    max_iterations: int = 10
    temperature: float = 0.7


@dataclass
class ExecutionContext:
    """执行上下文"""
    session_id: Optional[str] = None
    parent_execution_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tools: Optional[List[Tool]] = None
    skills: Optional[List["Skill"]] = None


@dataclass
class TokenUsage:
    """Token使用情况"""
    prompt: int = 0
    completion: int = 0
    total: int = 0


@dataclass
class ExecutionMetadata:
    """执行元数据"""
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    iterations: int = 0
    model: str = ""
    temperature: float = 0.7


@dataclass
class ExecutionResult:
    """执行结果"""
    id: str
    agent_id: str
    session_id: str
    input: str
    output: str
    messages: List[Message]
    tool_calls: List[ToolCall]
    tool_results: List[ToolResult]
    subagent_calls: List["SubagentCall"]
    metadata: ExecutionMetadata = field(default_factory=ExecutionMetadata)
    timestamp: datetime = field(default_factory=datetime.now)
    duration: float = 0.0


@dataclass
class StreamChunk:
    """流式响应块"""
    type: str  # "text", "error", "done", "tool_call"
    content: Optional[str] = None
    error: Optional[str] = None
    tool_call: Optional[ToolCall] = None


@dataclass
class Memory:
    """记忆"""
    content: str
    id: Optional[str] = None
    timestamp: Optional[datetime] = None
    type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Skill:
    """技能"""
    name: str
    description: str
    version: str
    tools: List[Tool] = field(default_factory=list)
    prompts: Optional[Dict[str, str]] = None
    initialize: Optional[Callable[[Dict[str, Any]], None]] = None


@dataclass
class SubagentCall:
    """子代理调用记录"""
    id: str
    subagent_id: str
    input: str
    result: ExecutionResult
    timestamp: datetime


@dataclass
class SubagentConfig:
    """子代理配置"""
    id: Optional[str] = None
    name: str = ""
    description: Optional[str] = None
    parent_agent_id: Optional[str] = None
    model: Optional[ModelConfig] = None
    tools: Optional[List[Tool]] = None
    skills: Optional[List[Skill]] = None
    memory: Optional[MemoryConfig] = None
    system_prompt: Optional[str] = None
    max_iterations: Optional[int] = None
    temperature: Optional[float] = None
    inherit_tools: bool = True
    inherit_skills: bool = True
    inherit_memory: bool = False


# 前向引用类型（用于解决循环导入）
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .agent import Agent as AgentType
    from .memory import MemoryStore as MemoryStoreType
else:
    AgentType = Any
    MemoryStoreType = Any



























































































