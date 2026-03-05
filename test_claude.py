#!/usr/bin/env python3
"""测试Claude Code基本功能"""
import subprocess
import os
import sys

# 清除环境变量
env = os.environ.copy()
env.pop('CLAUDECODE', None)

print("=== 测试Claude Code基本调用 ===")

# 测试基本调用
cmd = ['/home/linuxbrew/.linuxbrew/bin/claude', '-p', '--max-turns=1', 'Say hello']

try:
    result = subprocess.run(
        cmd,
        env=env,
        input='hi\n',
        capture_output=True,
        text=True,
        timeout=30
    )
    print("STDOUT:", result.stdout[:500] if result.stdout else "(empty)")
    print("STDERR:", result.stderr[:500] if result.stderr else "(empty)")
    print("Return code:", result.returncode)
except subprocess.TimeoutExpired:
    print("TIMEOUT!")
except Exception as e:
    print(f"Error: {e}")
