"""
测试上下文管理模块
"""

import pytest
from nanosdk.context import Context, ContextManager


class TestContext:
    """测试上下文类"""
    
    def test_default_values(self):
        ctx = Context()
        assert ctx.variables == {}
        assert ctx.parent_context_id is None
        assert ctx.root_context_id is None
    
    def test_set_and_get(self):
        ctx = Context()
        ctx.set("key", "value")
        assert ctx.get("key") == "value"
    
    def test_get_default(self):
        ctx = Context()
        assert ctx.get("nonexistent", "default") == "default"
    
    def test_delete(self):
        ctx = Context()
        ctx.set("key", "value")
        ctx.delete("key")
        assert ctx.get("key") is None
    
    def test_clear(self):
        ctx = Context()
        ctx.set("key1", "value1")
        ctx.set("key2", "value2")
        ctx.clear()
        assert ctx.variables == {}
    
    def test_to_dict(self):
        ctx = Context()
        ctx.set("key", "value")
        data = ctx.to_dict()
        assert data["variables"] == {"key": "value"}
        assert data["parent_context_id"] is None


class TestContextManager:
    """测试上下文管理器"""
    
    def test_create_context(self):
        manager = ContextManager()
        ctx = manager.create("ctx-1")
        
        assert ctx is not None
        assert manager.get("ctx-1") == ctx
    
    def test_create_with_parent(self):
        manager = ContextManager()
        parent = manager.create("parent")
        child = manager.create("child", parent_id="parent")
        
        assert child.parent_context_id == "parent"
        assert child.root_context_id == "parent"
    
    def test_get_nonexistent(self):
        manager = ContextManager()
        assert manager.get("nonexistent") is None
    
    def test_update(self):
        manager = ContextManager()
        manager.create("ctx-1")
        manager.update("ctx-1", {"key": "value"})
        
        ctx = manager.get("ctx-1")
        assert ctx.get("key") == "value"
    
    def test_update_nonexistent(self):
        manager = ContextManager()
        # Should not raise error
        manager.update("nonexistent", {"key": "value"})
    
    def test_delete(self):
        manager = ContextManager()
        manager.create("ctx-1")
        manager.delete("ctx-1")
        
        assert manager.get("ctx-1") is None
    
    def test_clear(self):
        manager = ContextManager()
        manager.create("ctx-1")
        manager.create("ctx-2")
        manager.clear()
        
        assert manager.get("ctx-1") is None
        assert manager.get("ctx-2") is None
    
    def test_list(self):
        manager = ContextManager()
        manager.create("ctx-1")
        manager.create("ctx-2")
        
        contexts = manager.list()
        assert len(contexts) == 2
        assert "ctx-1" in contexts
        assert "ctx-2" in contexts
