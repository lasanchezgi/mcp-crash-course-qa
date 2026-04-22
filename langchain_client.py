import asyncio
import os
import sys

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

load_dotenv()

llm = ChatOpenAI()

MATH_SERVER_PATH = os.path.join(os.path.dirname(__file__), "servers", "math_server.py")


async def main():
    client = MultiServerMCPClient(
        {
            "math": {
                "command": sys.executable,
                "args": [MATH_SERVER_PATH],
                "transport": "stdio",
            },
            "weather": {
                "url": "http://localhost:8000/sse",
                "transport": "sse",
            },
        }
    )
    tools = await client.get_tools()
    agent = create_react_agent(llm, tools)

    math_result = await agent.ainvoke({"messages": "What is 3 + 5? And what is 4 * 7?"})
    print("Math result:", math_result["messages"][-1].content)

    weather_result = await agent.ainvoke({"messages": "What is the weather in Tokyo?"})
    print("Weather result:", weather_result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
