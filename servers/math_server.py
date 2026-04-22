# math_server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Math")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    return a * b

@mcp.prompt()
def math_assistant_prompt() -> str:
    """A prompt that configures the assistant to solve math problems step by step"""
    return (
        "You are a math assistant. "
        "When solving problems, use the available tools (add, multiply) "
        "and explain each step clearly."
    )

if __name__ == "__main__":
    mcp.run(transport="stdio")