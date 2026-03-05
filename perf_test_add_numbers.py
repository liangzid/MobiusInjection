import time
import sys
sys.path.insert(0, '/home/liangzi/code/AgentCodingDoS')

from add_numbers import add_numbers

# 性能测试参数
ITERATIONS = 100000

# 预热
for _ in range(1000):
    add_numbers(1, 2)

# 正式测试
start_time = time.perf_counter()
for _ in range(ITERATIONS):
    add_numbers(1, 2)
end_time = time.perf_counter()

elapsed_time = end_time - start_time

print(f"=== add_numbers 函数性能测试 ===")
print(f"迭代次数: {ITERATIONS}")
print(f"总执行时间: {elapsed_time:.4f} 秒")
print(f"单次执行时间: {elapsed_time / ITERATIONS * 1_000_000:.2f} 微秒")
print(f"每秒执行次数: {ITERATIONS / elapsed_time:,.0f}")
