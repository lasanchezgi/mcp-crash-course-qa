from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Weather")

@mcp.tool()
async def get_weather(location: str) -> str:
    """Get weather for location."""
    return "Hot as hell"

@mcp.prompt()
def weather_assistant_prompt(location: str) -> str:
    """A prompt that asks for a weather report for a given location"""
    return f"Please provide a weather report for {location} using the available tools."

if __name__ == "__main__":
    mcp.run(transport="sse")