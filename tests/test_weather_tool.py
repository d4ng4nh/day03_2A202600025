"""
Unit tests for the Weather Tool.

Tests the get_weather functionality using both mock and local LLM providers.
"""

from src.core.llm_provider import LLMProvider
from src.tools.weather_tool import WeatherTool
import unittest
from unittest.mock import Mock, MagicMock
import os
import sys

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class MockLLMProvider(LLMProvider):
    """Mock LLM Provider for testing without running actual model inference."""

    def __init__(self, response_text: str = ""):
        super().__init__(model_name="test-model")
        self.response_text = response_text

    def generate(self, prompt: str, system_prompt=None):
        """Return a mock response."""
        return {
            "content": self.response_text,
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 80,
                "total_tokens": 130
            },
            "latency_ms": 100,
            "provider": "mock"
        }

    def stream(self, prompt: str, system_prompt=None):
        """Mock streaming - not used in these tests."""
        yield self.response_text


class TestWeatherTool(unittest.TestCase):
    """Test cases for WeatherTool."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_response = """Temperature: 22°C (72°F)
Condition: sunny
Humidity: 65%
Wind Speed: 10 km/h"""

        self.mock_llm = MockLLMProvider(self.mock_response)
        self.weather_tool = WeatherTool(self.mock_llm)

    def test_tool_initialization(self):
        """Test that the weather tool initializes correctly."""
        self.assertEqual(self.weather_tool.name, "get_weather")
        self.assertIn("weather", self.weather_tool.description.lower())
        self.assertEqual(self.weather_tool.llm.model_name, "test-model")

    def test_execute_basic(self):
        """Test basic execution of get_weather."""
        result = self.weather_tool.execute("San Francisco", "2024-01-15")

        self.assertEqual(result["location"], "San Francisco")
        self.assertEqual(result["date"], "2024-01-15")
        self.assertIn("temperature", result)
        self.assertIn("condition", result)
        self.assertIn("raw_response", result)

    def test_parse_weather_response_complete(self):
        """Test parsing a complete weather response."""
        parsed = self.weather_tool._parse_weather_response(
            self.mock_response, "Paris", "tomorrow")

        self.assertEqual(parsed["location"], "Paris")
        self.assertEqual(parsed["date"], "tomorrow")
        self.assertEqual(parsed["temperature"], "22°C (72°F)")
        self.assertEqual(parsed["condition"], "sunny")
        self.assertEqual(parsed["humidity"], "65%")
        self.assertEqual(parsed["wind_speed"], "10 km/h")

    def test_parse_weather_response_partial(self):
        """Test parsing a response with missing fields."""
        partial_response = """Temperature: 15°C (59°F)
Condition: cloudy"""

        parsed = self.weather_tool._parse_weather_response(
            partial_response, "London", "2024-02-01")

        self.assertEqual(parsed["temperature"], "15°C (59°F)")
        self.assertEqual(parsed["condition"], "cloudy")
        self.assertEqual(parsed["humidity"], "Not available")
        self.assertEqual(parsed["wind_speed"], "Not available")

    def test_parse_weather_response_empty(self):
        """Test parsing an empty or invalid response."""
        parsed = self.weather_tool._parse_weather_response(
            "Invalid response", "Berlin", "today")

        self.assertEqual(parsed["location"], "Berlin")
        self.assertEqual(parsed["date"], "today")
        self.assertEqual(parsed["temperature"], "Not available")
        self.assertEqual(parsed["condition"], "Not available")

    def test_execute_with_different_locations(self):
        """Test execution with various location formats."""
        test_locations = [
            "New York",
            "Tokyo, Japan",
            "Sydney",
            "São Paulo"
        ]

        for location in test_locations:
            result = self.weather_tool.execute(location, "2024-01-20")
            self.assertEqual(result["location"], location)
            self.assertIn("temperature", result)

    def test_execute_with_different_date_formats(self):
        """Test execution with various date formats."""
        test_dates = [
            "2024-01-15",
            "tomorrow",
            "next Monday",
            "2024-12-31"
        ]

        for date in test_dates:
            result = self.weather_tool.execute("Chicago", date)
            self.assertEqual(result["date"], date)

    def test_tool_dict_format(self):
        """Test that tool dictionary has correct format for agent integration."""
        tool_dict = self.weather_tool.to_tool_dict()

        self.assertIn("name", tool_dict)
        self.assertIn("description", tool_dict)
        self.assertIn("parameters", tool_dict)
        self.assertEqual(tool_dict["name"], "get_weather")
        self.assertIn("location", tool_dict["parameters"])
        self.assertIn("date", tool_dict["parameters"])

    def test_response_includes_metadata(self):
        """Test that response includes metadata like model name and latency."""
        result = self.weather_tool.execute("Seattle", "2024-01-25")

        self.assertIn("model", result)
        self.assertIn("latency_ms", result)
        self.assertEqual(result["model"], "test-model")
        self.assertEqual(result["latency_ms"], 100)

    def test_rainy_weather_response(self):
        """Test parsing rainy weather response."""
        rainy_response = """Temperature: 18°C (64°F)
Condition: rainy
Humidity: 85%
Wind Speed: 25 km/h"""

        parsed = self.weather_tool._parse_weather_response(
            rainy_response, "Seattle", "2024-02-10")

        self.assertEqual(parsed["condition"], "rainy")
        self.assertEqual(parsed["humidity"], "85%")
        self.assertGreater(int(parsed["wind_speed"].split()[0]), 20)

    def test_snowy_weather_response(self):
        """Test parsing snowy weather response."""
        snowy_response = """Temperature: -5°C (23°F)
Condition: snowy
Humidity: 70%
Wind Speed: 15 km/h"""

        parsed = self.weather_tool._parse_weather_response(
            snowy_response, "Montreal", "2024-01-10")

        self.assertEqual(parsed["condition"], "snowy")
        self.assertIn("-", parsed["temperature"])


class TestWeatherToolIntegration(unittest.TestCase):
    """Integration tests for WeatherTool (can be used with actual LocalProvider)."""

    def setUp(self):
        """Set up integration test fixtures."""
        self.mock_llm = MockLLMProvider("""Temperature: 20°C (68°F)
Condition: partly cloudy
Humidity: 60%
Wind Speed: 12 km/h""")
        self.weather_tool = WeatherTool(self.mock_llm)

    def test_full_workflow(self):
        """Test complete workflow: tool definition -> execution -> parsing."""
        # Get tool definition
        tool_def = self.weather_tool.to_tool_dict()
        self.assertEqual(tool_def["name"], "get_weather")

        # Execute tool
        result = self.weather_tool.execute("Boston", "2024-03-15")

        # Verify result structure
        self.assertIsInstance(result, dict)
        self.assertIn("location", result)
        self.assertIn("temperature", result)
        self.assertEqual(result["location"], "Boston")

    def test_multiple_calls(self):
        """Test that tool can handle multiple consecutive calls."""
        locations = ["Denver", "Phoenix", "San Diego"]

        results = []
        for location in locations:
            result = self.weather_tool.execute(location, "2024-03-20")
            results.append(result)

        self.assertEqual(len(results), 3)
        for i, location in enumerate(locations):
            self.assertEqual(results[i]["location"], location)


if __name__ == "__main__":
    unittest.main()
