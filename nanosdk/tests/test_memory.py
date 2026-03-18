"""
测试记忆模块
"""

import pytest
from datetime import datetime
from nanosdk.memory import InMemoryStore, HybridMemoryStore, create_memory_store
from nanosdk.types import Memory, MemoryConfig


class TestInMemoryStore:
    """测试内存存储"""
    
    @pytest.fixture
    def store(self):
        return InMemoryStore()
    
    @pytest.mark.asyncio
    async def test_add_memory(self, store):
        memory = Memory(content="Test content")
        result = await store.add(memory)
        
        assert result.id is not None
        assert result.timestamp is not None
        assert result.content == "Test content"
    
    @pytest.mark.asyncio
    async def test_get_memory(self, store):
        memory = Memory(content="Test content")
        added = await store.add(memory)
        
        retrieved = await store.get(added.id)
        assert retrieved is not None
        assert retrieved.content == "Test content"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent(self, store):
        result = await store.get("nonexistent")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_memory(self, store):
        memory = Memory(content="Test content")
        added = await store.add(memory)
        
        await store.delete(added.id)
        result = await store.get(added.id)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_search_with_query(self, store):
        await store.add(Memory(content="Python programming"))
        await store.add(Memory(content="JavaScript coding"))
        await store.add(Memory(content="Python basics"))
        
        results = await store.search("Python")
        
        assert len(results) == 2
        assert all("Python" in r.content for r in results)
    
    @pytest.mark.asyncio
    async def test_search_empty_query(self, store):
        await store.add(Memory(content="Content 1"))
        await store.add(Memory(content="Content 2"))
        
        results = await store.search("")
        
        assert len(results) == 2
    
    @pytest.mark.asyncio
    async def test_search_limit(self, store):
        for i in range(5):
            await store.add(Memory(content=f"Content {i}"))
        
        results = await store.search("", limit=3)
        
        assert len(results) == 3
    
    @pytest.mark.asyncio
    async def test_clear(self, store):
        await store.add(Memory(content="Test"))
        await store.clear()
        
        results = await store.search("")
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_session_memories(self, store):
        memory1 = Memory(content="Session 1", metadata={"session_id": "s1"})
        memory2 = Memory(content="Session 2", metadata={"session_id": "s2"})
        
        await store.add(memory1)
        await store.add(memory2)
        
        # Both should be searchable
        results = await store.search("Session")
        assert len(results) == 2


class TestHybridMemoryStore:
    """测试混合记忆存储"""
    
    @pytest.fixture
    def store(self):
        return HybridMemoryStore()
    
    @pytest.mark.asyncio
    async def test_add_and_search(self, store):
        memory = Memory(content="Test content")
        await store.add(memory)
        
        results = await store.search("Test")
        assert len(results) == 1
    
    @pytest.mark.asyncio
    async def test_get(self, store):
        memory = Memory(content="Test")
        added = await store.add(memory)
        
        retrieved = await store.get(added.id)
        assert retrieved is not None
        assert retrieved.content == "Test"


class TestCreateMemoryStore:
    """测试创建记忆存储"""
    
    def test_create_in_memory_store(self):
        config = MemoryConfig(type="short-term")
        store = create_memory_store(config)
        assert isinstance(store, InMemoryStore)
    
    def test_create_hybrid_store(self):
        config = MemoryConfig(type="hybrid")
        store = create_memory_store(config)
        assert isinstance(store, HybridMemoryStore)
    
    def test_create_default(self):
        store = create_memory_store()
        assert isinstance(store, InMemoryStore)
