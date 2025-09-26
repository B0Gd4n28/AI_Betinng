"""
Weather integration using OpenWeather API for match conditions
Provides temperature, wind, precipitation probability and conditions description
"""
from __future__ import annotations
import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.cache import cache
from utils.config import settings

logger = logging.getLogger(__name__)

class WeatherAPI:
    """
    OpenWeather API integration for football match weather conditions
    """
    
    def __init__(self):
        self.base_url = "https://api.openweathermap.org"
        self.geo_url = f"{self.base_url}/geo/1.0"
        self.weather_url = f"{self.base_url}/data/2.5"
        self.onecall_url = f"{self.base_url}/data/3.0"
    
    def _make_request(self, url: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Make OpenWeather API request with error handling"""
        if not settings.openweather_key:
            logger.debug("OpenWeather API key not configured")
            return None
            
        try:
            params["appid"] = settings.openweather_key
            response = requests.get(url, params=params, timeout=20)
            
            if response.status_code != 200:
                logger.error(f"OpenWeather error {response.status_code}: {response.text[:200]}")
                return None
                
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"OpenWeather request failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected OpenWeather error: {str(e)}")
            return None
    
    def _get_city_coordinates(self, city: str, country: str) -> Optional[tuple[float, float]]:
        """
        Get latitude and longitude for a city using geocoding API
        
        Args:
            city: City name (e.g., "London")
            country: Country code (e.g., "GB") or name (e.g., "United Kingdom")
            
        Returns:
            tuple[lat, lon] or None if not found
        """
        cache_key = f"geocode_{city}_{country}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Using cached coordinates for {city}, {country}")
            return cached_result
        
        # Try direct geocoding with city,country
        params = {"q": f"{city},{country}", "limit": 1}
        data = self._make_request(f"{self.geo_url}/direct", params)
        
        if data and len(data) > 0:
            location = data[0]
            coordinates = (location["lat"], location["lon"])
            
            # Cache coordinates for 24 hours (they don't change)
            cache.set(cache_key, coordinates, ttl=86400)
            
            return coordinates
        
        logger.warning(f"Could not find coordinates for {city}, {country}")
        return None
    
    def weather_for_city_at(self, city: str, country: str, iso_datetime: str) -> Dict[str, Any]:
        """
        Get weather conditions for a specific city and time
        
        Args:
            city: City name where match is played
            country: Country name or code
            iso_datetime: ISO datetime string for match time
            
        Returns:
            dict: {
                temp_c: float,
                wind_mps: float,
                pop: float,  # Probability of precipitation (0-1)
                desc: str,   # Weather description
                icon: str    # Weather icon code
            }
        """
        if not settings.openweather_key:
            return self._empty_weather()
        
        # Get coordinates first
        coordinates = self._get_city_coordinates(city, country)
        if not coordinates:
            return self._empty_weather()
        
        lat, lon = coordinates
        
        try:
            # Parse match datetime
            match_dt = datetime.fromisoformat(iso_datetime.replace('Z', '+00:00'))
            current_dt = datetime.now(match_dt.tzinfo)
            
            # Check if match is in the future (within 7 days for forecast)
            time_diff = (match_dt - current_dt).total_seconds()
            
            if time_diff > 7 * 24 * 3600:  # More than 7 days in future
                logger.debug(f"Match too far in future for forecast: {city}")
                return self._empty_weather()
            elif time_diff < -3600:  # More than 1 hour in the past
                logger.debug(f"Match in the past, using current weather: {city}")
                return self._get_current_weather(lat, lon)
            else:  # Match is within forecast range
                return self._get_forecast_weather(lat, lon, match_dt)
                
        except Exception as e:
            logger.error(f"Error parsing datetime or getting weather for {city}: {str(e)}")
            return self._empty_weather()
    
    def _get_current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get current weather conditions"""
        cache_key = f"current_weather_{lat}_{lon}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        params = {
            "lat": lat,
            "lon": lon,
            "units": "metric"
        }
        
        data = self._make_request(f"{self.weather_url}/weather", params)
        if not data:
            return self._empty_weather()
        
        result = {
            "temp_c": round(data["main"]["temp"], 1),
            "wind_mps": round(data["wind"].get("speed", 0.0), 1),
            "pop": 0.0,  # No precipitation probability for current weather
            "desc": data["weather"][0]["description"],
            "icon": data["weather"][0]["icon"]
        }
        
        # Cache current weather for 30 minutes
        cache.set(cache_key, result, ttl=1800)
        
        return result
    
    def _get_forecast_weather(self, lat: float, lon: float, match_dt: datetime) -> Dict[str, Any]:
        """Get forecast weather for match time"""
        cache_key = f"forecast_weather_{lat}_{lon}_{match_dt.isoformat()}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Try One Call API 3.0 first (requires subscription for forecasts)
        params = {
            "lat": lat,
            "lon": lon,
            "units": "metric",
            "exclude": "minutely,alerts"
        }
        
        data = self._make_request(f"{self.onecall_url}/onecall", params)
        
        if data and "hourly" in data:
            # Find closest hour to match time
            match_timestamp = match_dt.timestamp()
            best_forecast = None
            min_time_diff = float('inf')
            
            for hourly in data["hourly"][:24]:  # Check next 24 hours
                forecast_timestamp = hourly["dt"]
                time_diff = abs(forecast_timestamp - match_timestamp)
                
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    best_forecast = hourly
            
            if best_forecast and min_time_diff < 3600:  # Within 1 hour
                result = {
                    "temp_c": round(best_forecast["temp"], 1),
                    "wind_mps": round(best_forecast["wind_speed"], 1),
                    "pop": best_forecast.get("pop", 0.0),
                    "desc": best_forecast["weather"][0]["description"],
                    "icon": best_forecast["weather"][0]["icon"]
                }
                
                # Cache forecast for 2 hours
                cache.set(cache_key, result, ttl=7200)
                
                return result
        
        # Fallback to 5-day forecast API (free tier)
        params = {
            "lat": lat,
            "lon": lon,
            "units": "metric"
        }
        
        data = self._make_request(f"{self.weather_url}/forecast", params)
        if not data:
            return self._empty_weather()
        
        # Find closest forecast to match time
        match_timestamp = match_dt.timestamp()
        best_forecast = None
        min_time_diff = float('inf')
        
        for forecast in data.get("list", []):
            forecast_timestamp = forecast["dt"]
            time_diff = abs(forecast_timestamp - match_timestamp)
            
            if time_diff < min_time_diff:
                min_time_diff = time_diff
                best_forecast = forecast
        
        if best_forecast:
            result = {
                "temp_c": round(best_forecast["main"]["temp"], 1),
                "wind_mps": round(best_forecast["wind"].get("speed", 0.0), 1),
                "pop": best_forecast.get("pop", 0.0),
                "desc": best_forecast["weather"][0]["description"],
                "icon": best_forecast["weather"][0]["icon"]
            }
            
            # Cache forecast for 2 hours
            cache.set(cache_key, result, ttl=7200)
            
            return result
        
        return self._empty_weather()
    
    def _empty_weather(self) -> Dict[str, Any]:
        """Return empty weather data when API is unavailable"""
        return {
            "temp_c": None,
            "wind_mps": None,
            "pop": None,
            "desc": "n/a",
            "icon": "01d"  # Default clear sky icon
        }


# Global instance
weather_api = WeatherAPI()

# Convenience function for backward compatibility
def weather_for_city_at(city: str, country: str, iso_datetime: str) -> Dict[str, Any]:
    """Get weather conditions for a specific city and time"""
    return weather_api.weather_for_city_at(city, country, iso_datetime)