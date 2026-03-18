"""
记忆系统模块

支持短期记忆和长期记忆的存储、检索和管理
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .types import Memory, MemoryConfig


class MemoryStore(ABC):
    """记忆存储抽象基类"""
    
    @abstractmethod
    async def add(self, memory: Memory) -> Memory:
        """添加记忆"""
        pass
    
    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> List[Memory]:
        """搜索记忆"""
        pass
    
    @abstractmethod
    async def get(self, memory_id: str) -> Optional[Memory]:
        """获取记忆"""
        pass
    
    @abstractmethod
    async def delete(self, memory_id: str) -> None:
        """删除记忆"""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """清空所有记忆"""
        pass


@dataclass
class InMemoryStore(MemoryStore):
    """内存存储实现"""
    
    config: MemoryConfig = field(default_factory=lambda: MemoryConfig())
    _memories: Dict[str, Memory] = field(default_factory=dict)
    _session_memories: Dict[str, List[str]] = field(default_factory=dict)
    
    async def add(self, memory: Memory) -> Memory:
        """添加记忆"""
        if not memory.id:
            memory.id = str(uuid.uuid4())
        if not memory.timestamp:
            memory.timestamp = datetime.now()
        
        self._memories[memory.id] = memory
        
        session_id = memory.metadata.get("session_id", "default") if memory.metadata else "default"
        if session_id not in self._session_memories:
            self._session_memories[session_id] = []
        self._session_memories[session_id].append(memory.id)
        
        return memory
    
    async def search(self, query: str, limit: int = 10) -> List[Memory]:
        """搜索记忆"""
        if not query:
            memories = sorted(
                self._memories.values(),
                key=lambda m: m.timestamp or datetime.min,
                reverse=True
            )
            return memories[:limit]
        
        query_lower = query.lower()
        scored_memories = []
        
        for memory in self._memories.values():
            score = self._calculate_relevance(memory, query_lower)
            if score > 0:
                scored_memories.append((score, memory))
        
        scored_memories.sort(key=lambda x: (-x[0], -(x[1].timestamp or datetime.min).timestamp()))
        return [memory for _, memory in scored_memories[:limit]]
    
    async def get(self, memory_id: str) -> Optional[Memory]:
        """获取记忆"""
        return self._memories.get(memory_id)
    
    async def delete(self, memory_id: str) -> None:
        """删除记忆"""
        if memory_id in self._memories:
            memory = self._memories[memory_id]
            del self._memories[memory_id]
            
            session_id = memory.metadata.get("session_id", "default") if memory.metadata else "default"
            if session_id in self._session_memories:
                self._session_memories[session_id] = [
                    mid for mid in self._session_memories[session_id]
                    if mid != memory_id
                ]
    
    async def clear(self) -> None:
        """清空所有记忆"""
        self._memories.clear()
        self._session_memories.clear()
    
    def _calculate_relevance(self, memory: Memory, query_lower: str) -> float:
        """计算记忆与查询的相关性分数"""
        score = 0.0
        content_lower = memory.content.lower()
        
        if query_lower in content_lower:
            score += 0.5
            if content_lower == query_lower:
                score += 0.3
        
        query_words = query_lower.split()
        content_words = content_lower.split()
        matching_words = sum(1 for word in query_words if word in content_words)
        if query_words:
            score += (matching_words / len(query_words)) * 0.2
        
        if memory.type and query_lower in memory.type.lower():
            score += 0.1
        
        if memory.metadata:
            for value in memory.metadata.values():
                if isinstance(value, str) and query_lower in value.lower():
                    score += 0.05
        
        return min(score, 1.0)


@dataclass
class HybridMemoryStore(MemoryStore):
    """混合记忆存储"""
    
    config: MemoryConfig = field(default_factory=MemoryConfig)
    short_term: InMemoryStore = field(default_factory=InMemoryStore)
    
    async def add(self, memory: Memory) -> Memory:
        """添加记忆到短期存储"""
        return await self.short_term.add(memory)
    
    async def search(self, query: str, limit: int = 10) -> List[Memory]:
        """搜索记忆"""
        return await self.short_term.search(query, limit)
    
    async def get(self, memory_id: str) -> Optional[Memory]:
        """获取记忆"""
        return await self.short_term.get(memory_id)
    
    async def delete(self, memory_id: str) -> None:
        """删除记忆"""
        await self.short_term.delete(memory_id)
    
    async def clear(self) -> None:
        """清空所有记忆"""
        await self.short_term.clear()


def create_memory_store(config: Optional[MemoryConfig] = None) -> MemoryStore:
    """创建记忆存储"""
    config = config or MemoryConfig()
    
    if config.type == "hybrid":
        return HybridMemoryStore(config=config)
    else:
        return InMemoryStore(config=config)
