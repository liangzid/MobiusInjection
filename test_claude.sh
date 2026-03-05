#!/bin/bash
# 测试Claude Code基本功能

cd /home/liangzi/code/AgentCodingDoS

# 取消CLAUDECODE环境变量
unset CLAUDECODE

echo "=== 测试1: 基本调用 ==="
timeout 20 claude -p --max-turns=1 "Say hello" 2>&1

echo ""
echo "=== 测试完成 ==="
