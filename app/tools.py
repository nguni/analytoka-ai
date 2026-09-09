def calculator(a: float, b: float, operation: str) -> float:
    """
    Perform a mathematical calculation.

    Args:
        a: The first number.
        b: The second number.
        operation: The operation to perform.
                   Must be add, subtract, multiply, or divide.

    Returns:
        The result of the calculation.
    """

    if operation == "add":
        return a + b

    elif operation == "subtract":
        return a - b

    elif operation == "multiply":
        return a * b

    elif operation == "divide":
        if b == 0:
            raise ValueError("Cannot divide by zero")

        return a / b

    else:
        raise ValueError(f"Unknown operation: {operation}")