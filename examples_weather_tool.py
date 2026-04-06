"""
Example: Using the Weather Tool with Local LLM Provider.

This script demonstrates how to integrate the WeatherTool into the ReAct Agent
using the local Phi-3 model.
"""

import os
from src.core.local_provider import LocalProvider
from src.tools.weather_tool import WeatherTool


def main():
    """Example usage of the weather tool with local LLM."""

    # Initialize the local LLM provider with Phi-3 model
    model_path = "models/Phi-3-mini-4k-instruct-q4.gguf"

    if not os.path.exists(model_path):
        print(f"Error: Model file not found at {model_path}")
        print("Please ensure the Phi-3 model is downloaded in the models/ folder")
        return

    print("Loading local Phi-3 model...")
    llm = LocalProvider(model_path=model_path, n_ctx=2048)

    # Create the weather tool
    weather_tool = WeatherTool(llm)

    # Get tool definition (for use in agent)
    tool_def = weather_tool.to_tool_dict()
    print(f"\nTool Definition:")
    print(f"  Name: {tool_def['name']}")
    print(f"  Description: {tool_def['description']}")
    print(f"  Parameters: {tool_def['parameters']}")

    # Example 1: Get weather for a specific date
    print("\n" + "="*60)
    print("Example 1: Weather for San Francisco (specific date)")
    print("="*60)
    result1 = weather_tool.execute("San Francisco", "2024-01-15")
    print(f"Location: {result1['location']}")
    print(f"Date: {result1['date']}")
    print(f"Temperature: {result1['temperature']}")
    print(f"Condition: {result1['condition']}")
    print(f"Humidity: {result1['humidity']}")
    print(f"Wind Speed: {result1['wind_speed']}")
    print(f"Model: {result1['model']}")
    print(f"Latency: {result1['latency_ms']}ms")

    # Example 2: Get weather for tomorrow
    print("\n" + "="*60)
    print("Example 2: Weather for New York (tomorrow)")
    print("="*60)
    result2 = weather_tool.execute("New York", "tomorrow")
    print(f"Location: {result2['location']}")
    print(f"Date: {result2['date']}")
    print(f"Temperature: {result2['temperature']}")
    print(f"Condition: {result2['condition']}")
    print(f"Humidity: {result2['humidity']}")
    print(f"Wind Speed: {result2['wind_speed']}")

    # Example 3: Get weather for next week
    print("\n" + "="*60)
    print("Example 3: Weather for Tokyo (next week)")
    print("="*60)
    result3 = weather_tool.execute("Tokyo", "next Saturday")
    print(f"Location: {result3['location']}")
    print(f"Date: {result3['date']}")
    print(f"Temperature: {result3['temperature']}")
    print(f"Condition: {result3['condition']}")
    print(f"Humidity: {result3['humidity']}")
    print(f"Wind Speed: {result3['wind_speed']}")

    # Example 4: How to integrate into agent
    print("\n" + "="*60)
    print("Integration with Agent:")
    print("="*60)
    print("""
    # In your agent.py, you can add the weather tool like this:
    
    from src.tools.weather_tool import WeatherTool
    from src.core.local_provider import LocalProvider
    
    # Initialize LLM and tool
    llm = LocalProvider("models/Phi-3-mini-4k-instruct-q4.gguf")
    weather_tool = WeatherTool(llm)
    
    # Add to agent tools list
    tools = [
        weather_tool.to_tool_dict(),
        # ... other tools
    ]
    
    agent = ReActAgent(llm, tools)
    
    # When the agent calls the tool:
    # Action: get_weather("San Francisco", "2024-01-15")
    # The tool will execute and return structured weather data
    """)


if __name__ == "__main__":
    main()
