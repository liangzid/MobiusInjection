"""Factorial function implementation with error handling."""


def factorial(n: int) -> int:
    """
    Calculate the factorial of a non-negative integer.

    Args:
        n: A non-negative integer

    Returns:
        The factorial of n (n!)

    Raises:
        ValueError: If n is negative
        TypeError: If n is not an integer
    """
    if not isinstance(n, int):
        raise TypeError(f"Expected integer, got {type(n).__name__}")
    if n < 0:
        raise ValueError(f"Factorial is not defined for negative numbers: {n}")

    # Edge case: 0! = 1
    if n == 0:
        return 1

    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


if __name__ == "__main__":
    # Test cases
    test_cases = [0, 1, 5, 10]

    print("Factorial Function Tests")
    print("-" * 30)

    for num in test_cases:
        result = factorial(num)
        print(f"{num}! = {result}")

    print("-" * 30)

    # Test error handling
    print("Error handling tests:")

    try:
        factorial(-5)
    except ValueError as e:
        print(f"  Negative number: {e}")

    try:
        factorial(3.5)
    except TypeError as e:
        print(f"  Non-integer: {e}")

    try:
        factorial("five")
    except TypeError as e:
        print(f"  String input: {e}")
