"""
工具模块
"""

import json
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass

from .types import Tool, ToolCall, ToolResult, ToolContext, ToolParameterSchema


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
    
    def register(self, tool: Tool) -> None:
        """注册工具"""
        self._tools[tool.name] = tool
    
    def unregister(self, name: str) -> None:
        """注销工具"""
        if name in self._tools:
            del self._tools[name]
    
    def get(self, name: str) -> Optional[Tool]:
        """获取工具"""
        return self._tools.get(name)
    
    def list(self) -> List[Tool]:
        """列出所有工具"""
        return list(self._tools.values())
    
    def execute(
        self,
        name: str,
        arguments: Dict[str, Any],
        context: ToolContext
    ) -> ToolResult:
        """执行工具"""
        tool = self.get(name)
        if not tool:
            return ToolResult(
                tool_call_id="",
                name=name,
                result=None,
                error=f"Tool not found: {name}"
            )
        
        try:
            result = tool.execute(arguments, context)
            return ToolResult(
                tool_call_id="",
                name=name,
                result=result,
            )
        except Exception as e:
            return ToolResult(
                tool_call_id="",
                name=name,
                result=None,
                error=str(e)
            )
    
    def to_dict(self) -> List[Dict[str, Any]]:
        """转换为字典列表"""
        return [tool.to_dict() for tool in self.list()]
    
    def clear(self) -> None:
        """清空所有工具"""
        self._tools.clear()


def create_tool(
    name: str,
    description: str,
    parameters: Dict[str, Any],
    execute: Callable[[Dict[str, Any], ToolContext], Any]
) -> Tool:
    """
    创建工具
    
    Args:
        name: 工具名称
        description: 工具描述
        parameters: 参数模式
        execute: 执行函数
    
    Returns:
        Tool 实例
    """
    return Tool(
        name=name,
        description=description,
        parameters=ToolParameterSchema(**parameters),
        execute=execute
    )
