import add_numbers

# Test 1: Floating point addition
result1 = add_numbers.add_numbers(1.5, 2.5)
expected1 = 4.0
assert result1 == expected1, f"Test 1 failed: {result1} != {expected1}"
print(f"Test 1 passed: add_numbers(1.5, 2.5) = {result1}")

# Test 2: Negative numbers addition
result2 = add_numbers.add_numbers(-5, -3)
expected2 = -8
assert result2 == expected2, f"Test 2 failed: {result2} != {expected2}"
print(f"Test 2 passed: add_numbers(-5, -3) = {result2}")

# Test 3: Zero addition
result3 = add_numbers.add_numbers(0, 0)
expected3 = 0
assert result3 == expected3, f"Test 3 failed: {result3} != {expected3}"
print(f"Test 3 passed: add_numbers(0, 0) = {result3}")

# Test 4: Large numbers addition
result4 = add_numbers.add_numbers(10**10, 10**10)
expected4 = 2 * 10**10
assert result4 == expected4, f"Test 4 failed: {result4} != {expected4}"
print(f"Test 4 passed: add_numbers(10**10, 10**10) = {result4}")

print("\nAll tests passed!")
