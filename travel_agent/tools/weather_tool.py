import json
from tools.base import BaseTool
import logging
import httpx

logger = logging.getLogger(__name__)

class WeatherTool(BaseTool):
    
    @property
    def name()->str:
        return "get_weather"
    
    
    @property
    def description()->str:
        return "get weather of certain city"
    

    def execute(self, city: str) -> str:
        logger.info(f"search weather: {city}")
        
        url = f"https://wttr.in/{city}?format=j1"
        
        try:
            response = httpx.get(url, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            current_condition = data['current_condition'][0]
            weather_desc = current_condition['weatherDesc'][0]['value']
            temp_c = current_condition['temp_C']
            feels_like = current_condition['FeelsLikeC']
            humidity = current_condition['humidity']
            
            return (
                f"{city} current weather: {weather_desc}\n"
                f"🌡️ temperature: {temp_c}°C (feels{feels_like}°C)\n"
                f"💧 Humidity: {humidity}%\n"
                f"🌬️ Condition: {current_condition.get('windspeedKmph', 'N/A')} km/h"
            )
            
        except httpx.exceptions.RequestException as e:
            error_msg = f"network error: {e}"
            logger.error(error_msg)
            return error_msg
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            error_msg = f"data analysis error: {e}"
            logger.error(error_msg)
            return error_msg

