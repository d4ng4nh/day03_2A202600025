"""
Weather Tool using Local LLM Model.

This tool uses a local Phi-3 model to generate weather predictions for a given location and date.
"""

import re
from typing import Dict, Any, Optional
from src.core.llm_provider import LLMProvider


class WeatherTool:
    """
    A tool that uses a local LLM to predict weather for a given location and date.
    """

    def __init__(self, llm: LLMProvider):
        """
        Initialize the Weather Tool.

        Args:
            llm: An instance of LLMProvider (LocalProvider, OpenAI, etc.)
        """
        self.llm = llm
        self.name = "get_weather"
        self.description = "Get the weather forecast for a specific location on a given date"

    def execute(self, location: str, date: str) -> Dict[str, Any]:
        """
        Get weather information for a location on a specific date.

        Args:
            location: The location (e.g., "San Francisco", "New York")
            date: The date in format YYYY-MM-DD or descriptive (e.g., "tomorrow", "2024-01-15")

        Returns:
            Dictionary with weather information:
            {
                "location": str,
                "date": str,
                "temperature": str,
                "condition": str,
                "humidity": str,
                "wind_speed": str,
                "raw_response": str
            }
        """
        # Create a structured prompt for the LLM
        prompt = f"""Provide a weather forecast for {location} on {date}.
        
        Format your response with these exact labels on separate lines:
        Temperature: [value in Celsius and Fahrenheit]
        Condition: [sunny/cloudy/rainy/snowy/etc]
        Humidity: [percentage value]
        Wind Speed: [wind speed in km/h or mph]
        
        Keep the response concise and factual."""

        system_prompt = """You are a weather forecasting assistant. Provide accurate weather information 
        based on typical climate patterns and reasonable predictions. If you don't have actual data, 
        provide plausible forecasts based on the location and season."""

        # Call the LLM
        response = self.llm.generate(prompt, system_prompt)
        content = response["content"]

        # Parse the response
        parsed_weather = self._parse_weather_response(content, location, date)
        parsed_weather["raw_response"] = content
        parsed_weather["model"] = self.llm.model_name
        parsed_weather["latency_ms"] = response["latency_ms"]

        return parsed_weather

    def _parse_weather_response(self, response: str, location: str, date: str) -> Dict[str, Any]:
        """
        Parse the LLM response to extract structured weather data.

        Args:
            response: The raw response from the LLM
            location: The requested location
            date: The requested date

        Returns:
            Dictionary with parsed weather information
        """
        weather_dict = {
            "location": location,
            "date": date,
            "temperature": "Not available",
            "condition": "Not available",
            "humidity": "Not available",
            "wind_speed": "Not available"
        }

        # Extract temperature
        temp_match = re.search(
            r'Temperature:\s*(.+?)(?:\n|$)', response, re.IGNORECASE)
        if temp_match:
            weather_dict["temperature"] = temp_match.group(1).strip()

        # Extract condition
        condition_match = re.search(
            r'Condition:\s*(.+?)(?:\n|$)', response, re.IGNORECASE)
        if condition_match:
            weather_dict["condition"] = condition_match.group(1).strip()

        # Extract humidity
        humidity_match = re.search(
            r'Humidity:\s*(.+?)(?:\n|$)', response, re.IGNORECASE)
        if humidity_match:
            weather_dict["humidity"] = humidity_match.group(1).strip()

        # Extract wind speed
        wind_match = re.search(
            r'Wind\s*Speed:\s*(.+?)(?:\n|$)', response, re.IGNORECASE)
        if wind_match:
            weather_dict["wind_speed"] = wind_match.group(1).strip()

        return weather_dict

    def to_tool_dict(self) -> Dict[str, Any]:
        """
        Return tool definition as a dictionary for use in agent.

        Returns:
            Tool definition with name and description
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "location": "The location to get weather for",
                "date": "The date (YYYY-MM-DD format or descriptive like 'tomorrow')"
            }
        }
