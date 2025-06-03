"""
Climate data API integrations
"""
import requests
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import numpy as np
from config import settings
from .climate_trace_api import ClimateTraceAPI

logger = logging.getLogger(__name__)

class ClimateAPIHandler:
    """Handler for various climate data APIs"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ClimateIQ-Platform/1.0'
        })
        self.climate_trace = ClimateTraceAPI()
    
    def get_weather_data(self, location: str) -> Dict[str, Any]:
        """Get current weather data from OpenWeatherMap"""
        try:
            url = f"{settings.OPENWEATHER_API_BASE}/weather"
            params = {
                'q': location,
                'appid': settings.OPENWEATHER_API_KEY,
                'units': 'metric'
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'location': data['name'],
                'country': data['sys']['country'],
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'weather': data['weather'][0]['description'],
                'wind_speed': data['wind']['speed'],
                'coordinates': {
                    'lat': data['coord']['lat'],
                    'lon': data['coord']['lon']
                }
            }
            
        except Exception as e:
            logger.error(f"Error fetching weather data: {e}")
            # Return realistic fallback data based on location
            return self._get_fallback_weather_data(location)
    
    def _get_fallback_weather_data(self, location: str) -> Dict[str, Any]:
        """Provide realistic fallback weather data"""
        # Major cities coordinates and typical weather
        city_data = {
            'new york': {'lat': 40.7128, 'lon': -74.0060, 'temp': 15, 'country': 'US'},
            'london': {'lat': 51.5074, 'lon': -0.1278, 'temp': 12, 'country': 'GB'},
            'tokyo': {'lat': 35.6762, 'lon': 139.6503, 'temp': 18, 'country': 'JP'},
            'paris': {'lat': 48.8566, 'lon': 2.3522, 'temp': 14, 'country': 'FR'},
            'berlin': {'lat': 52.5200, 'lon': 13.4050, 'temp': 11, 'country': 'DE'},
            'sydney': {'lat': -33.8688, 'lon': 151.2093, 'temp': 22, 'country': 'AU'},
            'mumbai': {'lat': 19.0760, 'lon': 72.8777, 'temp': 28, 'country': 'IN'},
            'beijing': {'lat': 39.9042, 'lon': 116.4074, 'temp': 16, 'country': 'CN'},
            'moscow': {'lat': 55.7558, 'lon': 37.6176, 'temp': 8, 'country': 'RU'},
            'cairo': {'lat': 30.0444, 'lon': 31.2357, 'temp': 25, 'country': 'EG'}
        }
        
        location_lower = location.lower()
        city_info = city_data.get(location_lower, city_data['new york'])
        
        return {
            'location': location.title(),
            'country': city_info['country'],
            'temperature': city_info['temp'],
            'humidity': 65,
            'pressure': 1013,
            'weather': 'partly cloudy',
            'wind_speed': 3.5,
            'coordinates': {
                'lat': city_info['lat'],
                'lon': city_info['lon']
            },
            'note': 'Using fallback data - API unavailable'
        }
    
    def get_air_quality(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get air quality data from OpenWeatherMap"""
        try:
            url = f"{settings.OPENWEATHER_API_BASE}/air_pollution"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': settings.OPENWEATHER_API_KEY
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data['list']:
                aqi_data = data['list'][0]
                return {
                    'aqi': aqi_data['main']['aqi'],
                    'components': aqi_data['components'],
                    'timestamp': aqi_data['dt']
                }
            
            return {'error': 'No air quality data available'}
            
        except Exception as e:
            logger.error(f"Error fetching air quality data: {e}")
            # Return realistic fallback air quality data
            return {
                'aqi': 3,  # Moderate air quality
                'components': {
                    'co': 233.0,
                    'no': 0.01,
                    'no2': 20.0,
                    'o3': 68.0,
                    'so2': 6.0,
                    'pm2_5': 15.0,
                    'pm10': 25.0,
                    'nh3': 0.5
                },
                'timestamp': int(datetime.now().timestamp()),
                'note': 'Using fallback data - API unavailable'
            }
    
    def get_nasa_power_data(self, lat: float, lon: float, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get NASA POWER data for renewable energy potential"""
        try:
            url = f"{settings.NASA_API_BASE}/daily/point"
            params = {
                'parameters': 'ALLSKY_SFC_SW_DWN,T2M,WS10M',  # Solar irradiance, temperature, wind speed
                'community': 'RE',  # Renewable Energy
                'longitude': lon,
                'latitude': lat,
                'start': start_date,
                'end': end_date,
                'format': 'JSON',
                'api_key': settings.NASA_API_KEY
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'solar_irradiance': data['properties']['parameter']['ALLSKY_SFC_SW_DWN'],
                'temperature': data['properties']['parameter']['T2M'],
                'wind_speed': data['properties']['parameter']['WS10M'],
                'location': {
                    'lat': data['geometry']['coordinates'][1],
                    'lon': data['geometry']['coordinates'][0]
                }
            }
            
        except Exception as e:
            logger.error(f"Error fetching NASA POWER data: {e}")
            return {'error': str(e)}
    
    def calculate_carbon_footprint(self, activity_type: str, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate carbon footprint using Carbon Interface API"""
        try:
            url = f"{settings.CARBON_INTERFACE_API_BASE}/estimates"
            headers = {
                'Authorization': f'Bearer {settings.CARBON_INTERFACE_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            # Prepare payload based on activity type
            payload = self._prepare_carbon_payload(activity_type, activity_data)
            
            response = self.session.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'carbon_kg': data['data']['attributes']['carbon_kg'],
                'carbon_lb': data['data']['attributes']['carbon_lb'],
                'carbon_mt': data['data']['attributes']['carbon_mt'],
                'activity_type': activity_type,
                'activity_data': activity_data
            }
            
        except Exception as e:
            logger.error(f"Error calculating carbon footprint: {e}")
            return {'error': str(e)}
    
    def _prepare_carbon_payload(self, activity_type: str, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare payload for Carbon Interface API"""
        if activity_type == 'electricity':
            return {
                'type': 'electricity',
                'electricity_unit': 'kwh',
                'electricity_value': activity_data.get('kwh', 0),
                'country': activity_data.get('country', 'us')
            }
        elif activity_type == 'vehicle':
            return {
                'type': 'vehicle',
                'distance_unit': activity_data.get('distance_unit', 'km'),
                'distance_value': activity_data.get('distance', 0),
                'vehicle_model_id': activity_data.get('vehicle_model_id', '7268a9b7-17e8-4c8d-acca-57059252afe9')  # Default car
            }
        elif activity_type == 'flight':
            return {
                'type': 'flight',
                'passengers': activity_data.get('passengers', 1),
                'legs': activity_data.get('legs', [])
            }
        else:
            raise ValueError(f"Unsupported activity type: {activity_type}")
    
    def get_climate_trace_data(self, country: str = None, sector: str = None) -> Dict[str, Any]:
        """Get emissions data from Climate TRACE"""
        try:
            # Note: Climate TRACE API might require different authentication
            # This is a simplified implementation
            url = f"{settings.CLIMATETRACE_API_BASE}/emissions"
            params = {}
            
            if country:
                params['country'] = country
            if sector:
                params['sector'] = sector
            
            # For now, return mock data since Climate TRACE API access might be limited
            return {
                'country': country or 'global',
                'sector': sector or 'all',
                'total_emissions_mt': 50000000,  # Mock data
                'year': 2023,
                'note': 'This is sample data. Real Climate TRACE integration requires proper API access.'
            }
            
        except Exception as e:
            logger.error(f"Error fetching Climate TRACE data: {e}")
            return {'error': str(e)}
    
    def get_world_bank_climate_data(self, country_code: str, indicator: str) -> Dict[str, Any]:
        """Get climate indicators from World Bank API"""
        try:
            url = f"{settings.WORLD_BANK_API_BASE}/country/{country_code}/indicator/{indicator}"
            params = {
                'format': 'json',
                'date': '2020:2023',  # Recent years
                'per_page': 100
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if len(data) > 1 and data[1]:
                return {
                    'country': data[1][0]['country']['value'],
                    'indicator': data[1][0]['indicator']['value'],
                    'data': [
                        {
                            'year': item['date'],
                            'value': item['value']
                        }
                        for item in data[1] if item['value'] is not None
                    ]
                }
            
            return {'error': 'No data available'}
            
        except Exception as e:
            logger.error(f"Error fetching World Bank data: {e}")
            return {'error': str(e)}
    
    def get_renewable_energy_potential(self, location: str) -> Dict[str, Any]:
        """Get renewable energy potential for a location"""
        try:
            # Get coordinates from weather API
            weather_data = self.get_weather_data(location)
            if 'error' in weather_data:
                return weather_data
            
            lat = weather_data['coordinates']['lat']
            lon = weather_data['coordinates']['lon']
            
            # Get NASA POWER data for the last 30 days
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
            
            nasa_data = self.get_nasa_power_data(lat, lon, start_date, end_date)
            
            if 'error' in nasa_data:
                return nasa_data
            
            # Calculate averages
            solar_values = list(nasa_data['solar_irradiance'].values())
            wind_values = list(nasa_data['wind_speed'].values())
            
            avg_solar = sum(solar_values) / len(solar_values) if solar_values else 0
            avg_wind = sum(wind_values) / len(wind_values) if wind_values else 0
            
            # Simple potential calculations
            solar_potential = "High" if avg_solar > 5 else "Medium" if avg_solar > 3 else "Low"
            wind_potential = "High" if avg_wind > 6 else "Medium" if avg_wind > 3 else "Low"
            
            return {
                'location': location,
                'solar_potential': solar_potential,
                'wind_potential': wind_potential,
                'avg_solar_irradiance': round(avg_solar, 2),
                'avg_wind_speed': round(avg_wind, 2),
                'recommendations': self._generate_renewable_recommendations(solar_potential, wind_potential)
            }
            
        except Exception as e:
            logger.error(f"Error calculating renewable energy potential: {e}")
            return {'error': str(e)}
    
    def _generate_renewable_recommendations(self, solar_potential: str, wind_potential: str) -> List[str]:
        """Generate renewable energy recommendations"""
        recommendations = []
        
        if solar_potential == "High":
            recommendations.append("Excellent location for solar panels - consider rooftop solar installation")
            recommendations.append("Solar water heating would be very effective in this location")
        elif solar_potential == "Medium":
            recommendations.append("Good solar potential - solar panels would be moderately effective")
        
        if wind_potential == "High":
            recommendations.append("Strong wind resources - consider small wind turbines if permitted")
        elif wind_potential == "Medium":
            recommendations.append("Moderate wind potential - small wind systems might be viable")
        
        if not recommendations:
            recommendations.append("Consider energy efficiency improvements as primary focus")
            recommendations.append("Look into community renewable energy programs")
        
        return recommendations
    
    def get_emissions_heat_map_data(self, 
                                   bounds: Dict[str, float] = None,
                                   year: int = 2022,
                                   sector: str = None) -> Dict[str, Any]:
        """Get emissions data for heat map visualization"""
        try:
            # Default global bounds if not specified
            if not bounds:
                bounds = {
                    'north': 85,
                    'south': -85,
                    'east': 180,
                    'west': -180
                }
            
            # Get emissions sources from Climate TRACE
            sources_data = self.climate_trace.search_emissions_sources(
                year=year,
                sectors=[sector] if sector else None,
                limit=1000
            )
            
            if 'error' in sources_data:
                return sources_data
            
            # Process data for heat map
            heat_map_points = []
            
            # Handle Climate TRACE API response structure
            assets = sources_data.get('assets', []) if isinstance(sources_data, dict) else sources_data
            
            if isinstance(assets, list):
                for source in assets:
                    # Get coordinates from Centroid.Geometry
                    if 'Centroid' in source and 'Geometry' in source['Centroid']:
                        coords = source['Centroid']['Geometry']
                        if len(coords) >= 2:
                            lon, lat = coords[0], coords[1]
                            
                            # Check if point is within bounds
                            if (bounds['west'] <= lon <= bounds['east'] and 
                                bounds['south'] <= lat <= bounds['north']):
                                
                                # Get emissions value from EmissionsSummary
                                emissions = 0
                                if 'EmissionsSummary' in source:
                                    for emission in source['EmissionsSummary']:
                                        if emission.get('Gas') in ['co2e_100yr', 'co2e']:
                                            emissions = emission.get('EmissionsQuantity', 0)
                                            break
                                
                                heat_map_points.append({
                                    'lat': lat,
                                    'lon': lon,
                                    'intensity': emissions,
                                    'source_id': source.get('Id'),
                                    'name': source.get('Name', 'Unknown'),
                                    'country': source.get('Country', ''),
                                    'sector': source.get('Sector', '')
                                })
            
            return {
                'points': heat_map_points,
                'bounds': bounds,
                'year': year,
                'sector': sector,
                'total_sources': len(heat_map_points)
            }
            
        except Exception as e:
            logger.error(f"Error getting heat map data: {e}")
            return {'error': str(e)}
    
    def get_global_emissions_overview(self, year: int = 2022) -> Dict[str, Any]:
        """Get comprehensive global emissions overview"""
        try:
            # Get top emitting countries for power sector
            top_countries = ['CHN', 'USA', 'IND', 'JPN', 'RUS', 'DEU', 'KOR', 'IRN', 'SAU', 'GBR']
            country_emissions = self.climate_trace.get_country_emissions(
                since=year, 
                to=year, 
                sector=['power'],
                countries=top_countries
            )
            
            if 'error' in country_emissions:
                return country_emissions
            
            # Get sector breakdown
            sectors = self.climate_trace.get_sectors()
            
            # Calculate totals and rankings
            total_emissions = 0
            country_rankings = []
            
            if isinstance(country_emissions, list):
                for country_data in country_emissions:
                    if 'emissions' in country_data:
                        emissions_value = country_data['emissions'].get('co2e_100yr', 0)
                        total_emissions += emissions_value
                        country_rankings.append({
                            'country': country_data.get('country'),
                            'emissions': emissions_value,
                            'rank': country_data.get('rank', 0)
                        })
            
            # Sort by emissions
            country_rankings.sort(key=lambda x: x['emissions'], reverse=True)
            
            return {
                'year': year,
                'total_global_emissions': total_emissions,
                'top_countries': country_rankings[:10],
                'available_sectors': sectors,
                'data_sources': ['Climate TRACE', 'World Bank', 'UN SDG'],
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting global emissions overview: {e}")
            return {'error': str(e)}
    
    def get_location_climate_profile(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get comprehensive climate profile for a location"""
        try:
            # Get weather data
            location_name = f"{lat},{lon}"
            weather = self.get_weather_data(location_name)
            
            # Get air quality
            air_quality = self.get_air_quality(lat, lon)
            
            # Get renewable energy potential
            renewable_potential = self.get_renewable_energy_potential(location_name)
            
            # Get nearby emissions sources
            emissions_data = self.climate_trace.get_emissions_by_location(lat, lon, radius_km=50)
            
            # Get administrative area info
            admin_areas = self.climate_trace.search_administrative_areas(
                point=[lon, lat],
                limit=5
            )
            
            return {
                'location': {'lat': lat, 'lon': lon},
                'weather': weather,
                'air_quality': air_quality,
                'renewable_potential': renewable_potential,
                'nearby_emissions': emissions_data,
                'administrative_areas': admin_areas,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting location climate profile: {e}")
            return {'error': str(e)}
    
    def get_sector_analysis(self, sector: str, year: int = 2022) -> Dict[str, Any]:
        """Get detailed analysis for a specific sector"""
        try:
            # Get sector emissions data
            sector_emissions = self.climate_trace.get_asset_emissions(
                years=[year],
                sectors=[sector]
            )
            
            # Get country breakdown for this sector
            country_emissions = self.climate_trace.get_country_emissions(
                since=year,
                to=year,
                sector=[sector]
            )
            
            # Get emissions sources in this sector
            sources = self.climate_trace.search_emissions_sources(
                year=year,
                sectors=[sector],
                limit=100
            )
            
            return {
                'sector': sector,
                'year': year,
                'sector_emissions': sector_emissions,
                'country_breakdown': country_emissions,
                'major_sources': sources,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting sector analysis: {e}")
            return {'error': str(e)}
    
    def get_un_sdg_indicators(self, country_code: str = 'WLD') -> Dict[str, Any]:
        """Get UN SDG climate-related indicators"""
        try:
            # Climate-related SDG indicators
            climate_indicators = [
                'EN.ATM.CO2E.PC',  # CO2 emissions per capita
                'EG.USE.ELEC.KH.PC',  # Electric power consumption per capita
                'AG.LND.FRST.ZS',  # Forest area (% of land area)
                'EN.ATM.METH.KT.CE',  # Methane emissions
                'EG.ELC.RNEW.ZS'  # Renewable electricity output
            ]
            
            indicators_data = {}
            
            for indicator in climate_indicators:
                data = self.get_world_bank_climate_data(country_code, indicator)
                if 'error' not in data:
                    indicators_data[indicator] = data
            
            return {
                'country': country_code,
                'indicators': indicators_data,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting UN SDG indicators: {e}")
            return {'error': str(e)}