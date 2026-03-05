#!/usr/bin/env python3
"""测试Claude Code基本功能"""
import subprocess
import os

# 清除环境变量
env = os.environ.copy()
env.pop('CLAUDECODE', None)

print("=== 测试1: 直接运行claude --version ===")
result = subprocess.run(
    ['/home/linuxbrew/.linuxbrew/bin/claude', '--version'],
    env=env,
    capture_output=True,
    text=True,
    timeout=10
)
print("stdout:", result.stdout)
print("stderr:", result.stderr)
print("returncode:", result.returncode)

print("\n=== 测试2: 运行claude -p --max-turns=1 ===")
result = subprocess.run(
    'echo hi | /home/linuxbrew/.linuxbrew/bin/claude -p --max-turns=1',
    env=env,
    shell=True,
    capture_output=True,
    text=True,
    timeout=30
)
print("stdout:", result.stdout[:800] if result.stdout else "(empty)")
print("stderr:", result.stderr[:800] if result.stderr else "(empty)")
print("returncode:", result.returncode)
