"""
Comprehensive Climate TRACE API integration based on OpenAPI v6 specification
"""
import requests
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json
from config import settings

logger = logging.getLogger(__name__)

class ClimateTraceAPI:
    """Comprehensive Climate TRACE API client based on v6 specification"""
    
    def __init__(self):
        self.base_url = settings.CLIMATETRACE_API_BASE
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ClimateIQ-Platform/1.0',
            'Accept': 'application/json'
        })
    
    def search_emissions_sources(self, 
                                limit: int = 100,
                                year: int = 2022,
                                offset: int = 0,
                                countries: Optional[List[str]] = None,
                                sectors: Optional[List[str]] = None,
                                subsectors: Optional[List[str]] = None,
                                continents: Optional[List[str]] = None,
                                groups: Optional[List[str]] = None,
                                admin_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Search emissions sources using /v6/assets endpoint
        """
        try:
            url = f"{self.base_url}/assets"
            params = {
                'limit': min(limit, 1000),
                'year': year,
                'offset': offset
            }
            
            if countries:
                params['countries'] = ','.join(countries)
            if sectors:
                params['sectors'] = ','.join(sectors)
            if subsectors:
                params['subsectors'] = ','.join(subsectors)
            if continents:
                params['continents'] = ','.join(continents)
            if groups:
                params['groups'] = ','.join(groups)
            if admin_id:
                params['adminId'] = admin_id
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error searching emissions sources: {e}")
            return {'error': str(e)}
    
    def get_source_details(self, source_id: int) -> Dict[str, Any]:
        """
        Get details on a single emissions source using /v6/assets/{sourceId}
        """
        try:
            if not (1 <= source_id <= 5000000):
                return {'error': 'Source ID must be between 1 and 5,000,000'}
            
            url = f"{self.base_url}/assets/{source_id}"
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting source details for ID {source_id}: {e}")
            return {'error': str(e)}
    
    def get_asset_emissions(self,
                           years: Optional[List[int]] = None,
                           admin_id: Optional[int] = None,
                           subsectors: Optional[List[str]] = None,
                           sectors: Optional[List[str]] = None,
                           continents: Optional[List[str]] = None,
                           groups: Optional[List[str]] = None,
                           countries: Optional[List[str]] = None,
                           gas: Optional[str] = None) -> Dict[str, Any]:
        """
        Filter and summarize source emissions using /v6/assets/emissions
        """
        try:
            url = f"{self.base_url}/assets/emissions"
            params = {}
            
            if years:
                params['years'] = ','.join(map(str, years))
            if admin_id:
                params['adminId'] = admin_id
            if subsectors:
                params['subsectors'] = ','.join(subsectors)
            if sectors:
                params['sectors'] = ','.join(sectors)
            if continents:
                params['continents'] = ','.join(continents)
            if groups:
                params['groups'] = ','.join(groups)
            if countries:
                params['countries'] = ','.join(countries)
            if gas:
                params['gas'] = gas
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting asset emissions: {e}")
            return {'error': str(e)}
    
    def get_country_emissions(self,
                             since: int = 2010,
                             to: int = 2020,
                             sector: Optional[List[str]] = None,
                             subsector: Optional[List[str]] = None,
                             continents: Optional[List[str]] = None,
                             groups: Optional[List[str]] = None,
                             countries: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get emissions summarized by country using /v6/country/emissions
        """
        try:
            url = f"{self.base_url}/country/emissions"
            params = {
                'since': max(2000, min(since, 2050)),
                'to': max(2000, min(to, 2050))
            }
            
            if sector:
                params['sector'] = ','.join(sector)
            if subsector:
                params['subsectors'] = ','.join(subsector)
            if continents:
                params['continents'] = ','.join(continents)
            if groups:
                params['groups'] = ','.join(groups)
            if countries:
                params['countries'] = ','.join(countries)
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting country emissions: {e}")
            return {'error': str(e)}
    
    def search_administrative_areas(self,
                                   limit: int = 100,
                                   offset: int = 0,
                                   point: Optional[List[float]] = None,
                                   bbox: Optional[List[float]] = None,
                                   name: Optional[str] = None,
                                   level: Optional[int] = None) -> Dict[str, Any]:
        """
        Search for administrative areas using /v6/admins/search
        """
        try:
            url = f"{self.base_url}/admins/search"
            params = {
                'limit': min(limit, 1000),
                'offset': offset
            }
            
            if point and len(point) == 2:
                params['point'] = f"{point[0]},{point[1]}"
            if bbox and len(bbox) == 4:
                params['bbox'] = ','.join(map(str, bbox))
            if name:
                params['name'] = name[:50]  # Max 50 characters
            if level is not None and 0 <= level <= 2:
                params['level'] = level
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error searching administrative areas: {e}")
            return {'error': str(e)}
    
    def get_admin_geojson(self, admin_id: Union[int, str]) -> Dict[str, Any]:
        """
        Get administrative area GeoJSON using /v6/admins/{adminId}/geojson
        """
        try:
            url = f"{self.base_url}/admins/{admin_id}/geojson"
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting admin GeoJSON for ID {admin_id}: {e}")
            return {'error': str(e)}
    
    def get_sectors(self) -> Dict[str, Any]:
        """
        Get sector definitions using /v6/definitions/sectors
        """
        try:
            url = f"{self.base_url}/definitions/sectors"
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting sectors: {e}")
            return {'error': str(e)}
    
    def get_subsectors(self) -> Dict[str, Any]:
        """
        Get subsector definitions using /v6/definitions/subsectors
        """
        try:
            url = f"{self.base_url}/definitions/subsectors"
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting subsectors: {e}")
            return {'error': str(e)}
    
    def get_countries(self) -> Dict[str, Any]:
        """
        Get country definitions using /v6/definitions/countries
        """
        try:
            url = f"{self.base_url}/definitions/countries"
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting countries: {e}")
            return {'error': str(e)}
    
    def get_groups(self) -> Dict[str, Any]:
        """
        Get country group definitions using /v6/definitions/groups
        """
        try:
            url = f"{self.base_url}/definitions/groups"
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting groups: {e}")
            return {'error': str(e)}
    
    def get_continents(self) -> Dict[str, Any]:
        """
        Get continent definitions using /v6/definitions/continents
        """
        try:
            url = f"{self.base_url}/definitions/continents"
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting continents: {e}")
            return {'error': str(e)}
    
    def get_gases(self) -> Dict[str, Any]:
        """
        Get gas definitions using /v6/definitions/gases
        """
        try:
            url = f"{self.base_url}/definitions/gases"
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting gases: {e}")
            return {'error': str(e)}
    
    def get_global_emissions_summary(self, year: int = 2022) -> Dict[str, Any]:
        """
        Get a comprehensive global emissions summary
        """
        try:
            # Get emissions by country
            country_emissions = self.get_country_emissions(since=year, to=year)
            
            # Get emissions by sector
            asset_emissions = self.get_asset_emissions(years=[year])
            
            # Get available sectors and countries
            sectors = self.get_sectors()
            countries = self.get_countries()
            
            return {
                'year': year,
                'country_emissions': country_emissions,
                'asset_emissions': asset_emissions,
                'available_sectors': sectors,
                'available_countries': countries,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting global emissions summary: {e}")
            return {'error': str(e)}
    
    def get_emissions_by_location(self, lat: float, lon: float, radius_km: int = 50) -> Dict[str, Any]:
        """
        Get emissions data for a specific location using bounding box
        """
        try:
            # Create bounding box around the point (approximate)
            lat_offset = radius_km / 111.0  # Rough conversion km to degrees
            lon_offset = radius_km / (111.0 * abs(lat))  # Adjust for latitude
            
            bbox = [
                lon - lon_offset,  # min_lon
                lat - lat_offset,  # min_lat
                lon + lon_offset,  # max_lon
                lat + lat_offset   # max_lat
            ]
            
            # Search for administrative areas in the region
            admin_areas = self.search_administrative_areas(bbox=bbox, limit=10)
            
            # Get emissions sources in the area
            emissions_sources = self.search_emissions_sources(limit=50)
            
            return {
                'location': {'lat': lat, 'lon': lon},
                'radius_km': radius_km,
                'administrative_areas': admin_areas,
                'emissions_sources': emissions_sources,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting emissions by location: {e}")
            return {'error': str(e)}