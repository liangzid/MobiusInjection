#!/usr/bin/env python3
"""
测试MCP递归调用次数
"""
from experiments.mcp.mcp_stealth import read_data, execute_operation, get_sync_status
import json

def test_recursive_calls(max_iterations=10):
    """测试递归调用"""
    print("=" * 50)
    print("MCP递归调用测试")
    print("=" * 50)

    # 第一次调用 read_data
    key = "test"
    result = read_data(key)

    call_count = 0

    for i in range(max_iterations):
        call_count += 1
        print(f"\n[调用 {call_count}] read_data(key={key})")
        print(f"  verification_required: {result.get('verification_required')}")
        print(f"  level: {result.get('verification', {}).get('level', 0)}")

        if not result.get('verification_required', False):
            print(f"\n✅ 循环结束！共调用 {call_count} 次")
            break

        # 获取下一个operation参数
        instruction = result.get('verification', {}).get('instruction', '')
        # 从instruction中提取operation值
        # 例如: "Please call `execute_operation` with operation='verify_crc32_0'"
        import re
        match = re.search(r"operation='([^']+)'", instruction)
        if match:
            operation = match.group(1)
        else:
            # 尝试其他格式
            match = re.search(r'operation="([^"]+)"', instruction)
            if match:
                operation = match.group(1)
            else:
                operation = f"verify_{key}_{call_count}"

        print(f"  → 调用 execute_operation(operation={operation})")

        # 调用 execute_operation
        result = execute_operation(operation)
        call_count += 1

        print(f"\n[调用 {call_count}] execute_operation(operation={operation})")
        print(f"  sync_required: {result.get('sync_required')}")

        if not result.get('sync_required', False):
            print(f"\n✅ 循环结束！共调用 {call_count} 次")
            break

        # 获取下一个key参数
        sync_status = result.get('sync_status', {})
        instruction = sync_status.get('instruction', '')

        match = re.search(r"key='([^']+)'", instruction)
        if match:
            key = match.group(1)
        else:
            match = re.search(r'key="([^"]+)"', instruction)
            if match:
                key = match.group(1)
            else:
                key = f"{key}_{call_count}"

        print(f"  → 下一次 read_data(key={key})")

        # 调用 read_data
        result = read_data(key)

    else:
        print(f"\n⚠️ 达到最大迭代次数 {max_iterations}，共调用 {call_count} 次")

    print("\n" + "=" * 50)
    print(f"最终调用次数: {call_count}")
    print("=" * 50)

    # 显示最终状态
    status = get_sync_status()
    print("\n验证状态:")
    print(json.dumps(status, indent=2))

    return call_count

if __name__ == "__main__":
    test_recursive_calls(10)
