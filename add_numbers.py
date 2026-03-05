def add_numbers(a: float | int, b: float | int) -> float | int:
    """Add two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        The sum of a and b

    Raises:
        TypeError: If inputs are not numeric
    """
    if not isinstance(a, (int, float)):
        raise TypeError(f"Expected numeric value for a, got {type(a).__name__}")
    if not isinstance(b, (int, float)):
        raise TypeError(f"Expected numeric value for b, got {type(b).__name__}")
    return a + b
