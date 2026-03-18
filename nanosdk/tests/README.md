# ReAct Agent 测试

本目录包含 nanosdk ReAct Agent 的测试用例。

## 测试文件

| 文件 | 说明 |
|------|------|
| `test_simple.py` | 简单测试（无需 pytest，直接运行） |
| `test_react_agent.py` | pytest 测试用例（需要安装 pytest） |
| `run_tests.py` | pytest 运行脚本 |

## 运行测试

### 方法 1: 简单测试（推荐）

无需安装额外依赖：

```bash
cd /home/admin/.openclaw/workspace/nanosdk-react/nanosdk/tests
python test_simple.py
```

### 方法 2: pytest 测试

需要安装 pytest：

```bash
pip install pytest pytest-asyncio

cd /home/admin/.openclaw/workspace/nanosdk-react/nanosdk/tests
python run_tests.py -v
```

或直接使用 pytest：

```bash
pytest test_react_agent.py -v
```

## 测试覆盖

### 基础功能测试
- ✅ Agent 初始化
- ✅ 工具注册/注销
- ✅ Agent 状态转换

### ReAct 循环测试
- ✅ 无工具调用的执行
- ✅ 带工具调用的执行
- ✅ 最大迭代次数限制
- ✅ 进度回调

### 消息历史测试
- ✅ 消息历史更新
- ✅ 消息历史清空
- ✅ 消息历史修剪

### 执行上下文测试
- ✅ 上下文创建
- ✅ 工具合并
- ✅ Session ID 传递

### 流式执行测试
- ✅ Stream 响应

### 集成测试
- ✅ 完整工作流
- ✅ 并发执行

### 边界条件测试
- ✅ 空输入
- ✅ 长输入
- ✅ 特殊字符
- ✅ Unicode 输入

## 测试工具

测试中使用的模拟工具：

1. **calculator** - 数学计算工具
2. **search** - 搜索工具（异步）
3. **weather** - 天气查询工具
4. **failing_tool** - 故意失败的工具（用于错误测试）

## 添加新测试

参考现有测试格式：

```python
async def test_your_feature():
    """测试你的功能"""
    print("\n[Test] Your Feature")
    
    config = AgentConfig(...)
    agent = Agent(config)
    
    # 执行测试
    result = await agent.execute("test")
    
    # 验证结果
    assert result.output is not None
    print("  ✓ Test passed")
```

然后添加到 `run_all_tests()` 列表中。
