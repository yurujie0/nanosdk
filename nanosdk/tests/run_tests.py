"""
运行 ReAct Agent 测试

使用方法:
    python run_tests.py          # 运行所有测试
    python run_tests.py -v       # 详细输出
    python run_tests.py -k test_name  # 运行特定测试
"""

import sys
import subprocess


def main():
    """运行 pytest 测试"""
    # 构建 pytest 命令
    cmd = ["python", "-m", "pytest", "test_react_agent.py"]
    
    # 添加传入的参数
    cmd.extend(sys.argv[1:])
    
    # 运行测试
    result = subprocess.run(cmd, cwd="/home/admin/.openclaw/workspace/nanosdk-react/nanosdk/tests")
    
    return result.returncode


if __name__ == "__main__":
    exit(main())
