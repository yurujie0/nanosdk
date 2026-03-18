"""
上下文管理模块
"""

from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class Context:
    """执行上下文"""
    variables: Dict[str, Any] = field(default_factory=dict)
    parent_context_id: Optional[str] = None
    root_context_id: Optional[str] = None
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取变量"""
        return self.variables.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """设置变量"""
        self.variables[key] = value
    
    def delete(self, key: str) -> None:
        """删除变量"""
        if key in self.variables:
            del self.variables[key]
    
    def clear(self) -> None:
        """清空所有变量"""
        self.variables.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "variables": self.variables,
            "parent_context_id": self.parent_context_id,
            "root_context_id": self.root_context_id,
        }


class ContextManager:
    """上下文管理器"""
    
    def __init__(self):
        self._contexts: Dict[str, Context] = {}
        self._lock = Lock()
    
    def create(self, context_id: str, parent_id: Optional[str] = None) -> Context:
        """创建新上下文"""
        with self._lock:
            root_id = None
            if parent_id and parent_id in self._contexts:
                parent = self._contexts[parent_id]
                root_id = parent.root_context_id or parent_id
            
            context = Context(
                parent_context_id=parent_id,
                root_context_id=root_id,
            )
            self._contexts[context_id] = context
            return context
    
    def get(self, context_id: str) -> Optional[Context]:
        """获取上下文"""
        return self._contexts.get(context_id)
    
    def update(self, context_id: str, variables: Dict[str, Any]) -> None:
        """更新上下文变量"""
        with self._lock:
            if context_id in self._contexts:
                self._contexts[context_id].variables.update(variables)
    
    def delete(self, context_id: str) -> None:
        """删除上下文"""
        with self._lock:
            if context_id in self._contexts:
                del self._contexts[context_id]
    
    def clear(self) -> None:
        """清空所有上下文"""
        with self._lock:
            self._contexts.clear()
    
    def list(self) -> Dict[str, Context]:
        """列出所有上下文"""
        return self._contexts.copy()
