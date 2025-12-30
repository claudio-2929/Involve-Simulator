"""
WindField Module - Stratified Wind Model for Stratospheric Navigation

Based on Project Loon's approach to wind-based navigation:
- Wind vectors vary significantly with altitude in the stratosphere
- The platform can change altitude to find favorable wind directions
- Seasonal and latitudinal patterns affect wind behavior

Altitude layers (18-25km):
- 18-19km: Often easterly trade winds (lower stratosphere)
- 20-21km: Transition zone, variable
- 22-23km: Often westerly, stronger
- 24-25km: High stratosphere, typically westerly, very strong in winter
"""

import math
import random
from typing import Tuple, Dict, List
from dataclasses import dataclass


@dataclass
class WindVector:
    """Wind vector at a specific point."""
    speed_kmh: float
    direction_deg: float  # 0=North, 90=East, 180=South, 270=West
    altitude_km: float
    
    def get_components(self) -> Tuple[float, float]:
        """Returns (east_component, north_component) in km/h."""
        rad = math.radians(self.direction_deg)
        east = self.speed_kmh * math.sin(rad)
        north = self.speed_kmh * math.cos(rad)
        return east, north


class WindField:
    """
    Stratified wind model for the stratosphere.
    
    Simulates realistic wind variation with altitude based on:
    - Quasi-Biennial Oscillation (QBO) patterns
    - Seasonal variations (polar vortex in winter)
    - Latitude-dependent behavior
    """
    
    # Altitude layers for wind model (km)
    ALTITUDE_LAYERS = [18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0]
    
    # Base wind patterns by altitude (speed_kmh, direction_deg_offset)
    # Direction offset: 0 = aligned with latitude flow, varies by layer
    BASE_WIND_PATTERN = {
        18.0: (15, 90),   # Easterly, moderate
        19.0: (12, 75),   # East-Northeast, weaker
        20.0: (10, 0),    # Variable/Northerly, transition
        21.0: (18, 270),  # Westerly, strengthening
        22.0: (25, 260),  # Westerly, strong
        23.0: (30, 255),  # West-Southwest, stronger
        24.0: (35, 250),  # Strong westerly
        25.0: (40, 245),  # Very strong westerly
    }
    
    @classmethod
    def get_wind_vector(
        cls, 
        lat: float, 
        lon: float, 
        altitude_km: float, 
        month: int,
        add_noise: bool = True
    ) -> WindVector:
        """
        Get wind vector at specified location and altitude.
        
        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees (currently unused, for future regional models)
            altitude_km: Altitude in kilometers (18-25km valid range)
            month: Month 1-12
            add_noise: Whether to add stochastic variation
            
        Returns:
            WindVector with speed and direction
        """
        # Clamp altitude to valid range
        alt = max(18.0, min(25.0, altitude_km))
        
        # Find closest altitude layer
        closest_layer = min(cls.ALTITUDE_LAYERS, key=lambda x: abs(x - alt))
        base_speed, base_dir = cls.BASE_WIND_PATTERN[closest_layer]
        
        # Seasonal modifier (winter = stronger winds)
        winter_factor = cls._get_seasonal_factor(lat, month)
        
        # Latitude modifier (higher = more variable, stronger in jet stream)
        lat_factor = cls._get_latitude_factor(lat)
        
        # Apply modifiers
        speed = base_speed * winter_factor * lat_factor
        
        # Direction shifts with latitude and season
        direction = (base_dir + (lat * 0.5) + (month * 3)) % 360
        
        # Add stochastic noise for realism
        if add_noise:
            speed *= random.uniform(0.8, 1.2)
            direction = (direction + random.uniform(-15, 15)) % 360
        
        return WindVector(
            speed_kmh=round(speed, 1),
            direction_deg=round(direction, 1),
            altitude_km=alt
        )
    
    @classmethod
    def get_wind_profile(
        cls, 
        lat: float, 
        lon: float, 
        month: int
    ) -> Dict[float, WindVector]:
        """
        Get wind vectors at all altitude layers.
        
        Returns:
            Dict mapping altitude_km to WindVector
        """
        return {
            alt: cls.get_wind_vector(lat, lon, alt, month, add_noise=False)
            for alt in cls.ALTITUDE_LAYERS
        }
    
    @classmethod
    def get_optimal_altitude(
        cls,
        lat: float,
        lon: float,
        target_heading_deg: float,
        month: int,
        altitude_range: Tuple[float, float] = (18.0, 25.0)
    ) -> Tuple[float, float]:
        """
        Find the altitude with wind direction closest to target heading.
        
        This is the core of Loon-style navigation: find the altitude
        where wind direction will push the platform toward the target.
        
        Args:
            lat, lon: Current position
            target_heading_deg: Desired direction of travel (0=N, 90=E)
            month: Current month
            altitude_range: Valid altitude range for platform
            
        Returns:
            Tuple of (optimal_altitude_km, heading_error_deg)
        """
        best_alt = altitude_range[0]
        best_error = 180.0
        
        for alt in cls.ALTITUDE_LAYERS:
            if altitude_range[0] <= alt <= altitude_range[1]:
                wind = cls.get_wind_vector(lat, lon, alt, month, add_noise=False)
                
                # Wind direction is where wind is COMING FROM
                # Platform moves WITH the wind, so travel direction = wind_dir + 180
                travel_direction = (wind.direction_deg + 180) % 360
                
                # Calculate heading error (absolute angular difference)
                error = abs(target_heading_deg - travel_direction)
                if error > 180:
                    error = 360 - error
                
                if error < best_error:
                    best_error = error
                    best_alt = alt
        
        return best_alt, best_error
    
    @classmethod
    def _get_seasonal_factor(cls, lat: float, month: int) -> float:
        """
        Calculate seasonal wind intensity factor.
        
        Winter months have stronger stratospheric winds due to polar vortex.
        """
        is_northern = lat > 0
        
        # Winter months for each hemisphere
        if is_northern:
            winter_months = [11, 12, 1, 2, 3]
        else:
            winter_months = [5, 6, 7, 8, 9]
        
        if month in winter_months:
            # Winter: 30-80% stronger winds
            return 1.3 + 0.5 * (abs(lat) / 90.0)
        else:
            # Summer: baseline or slightly weaker
            return 0.9 + 0.1 * (abs(lat) / 90.0)
    
    @classmethod
    def _get_latitude_factor(cls, lat: float) -> float:
        """
        Calculate latitude-dependent wind factor.
        
        Mid-latitudes (30-60°) are in the jet stream zone = stronger winds.
        Equator and poles are relatively calmer.
        """
        abs_lat = abs(lat)
        
        if 30 <= abs_lat <= 60:
            # Jet stream zone: stronger
            return 1.2 + 0.3 * ((abs_lat - 30) / 30)
        elif abs_lat < 30:
            # Tropics: weaker but steady
            return 0.7 + 0.5 * (abs_lat / 30)
        else:
            # Polar: moderate
            return 1.0
    
    @classmethod
    def simulate_drift(
        cls,
        start_lat: float,
        start_lon: float,
        altitude_km: float,
        hours: float,
        month: int
    ) -> Tuple[float, float, float]:
        """
        Simulate platform drift over time at fixed altitude.
        
        Args:
            start_lat, start_lon: Starting position
            altitude_km: Fixed altitude
            hours: Duration in hours
            month: Current month
            
        Returns:
            Tuple of (new_lat, new_lon, distance_km)
        """
        wind = cls.get_wind_vector(start_lat, start_lon, altitude_km, month)
        east_kmh, north_kmh = wind.get_components()
        
        # Calculate displacement
        east_km = east_kmh * hours
        north_km = north_kmh * hours
        
        # Convert to lat/lon (approximate, assumes small distances)
        # 1 degree latitude ≈ 111 km
        # 1 degree longitude ≈ 111 km * cos(lat)
        delta_lat = north_km / 111.0
        delta_lon = east_km / (111.0 * max(0.1, math.cos(math.radians(start_lat))))
        
        new_lat = start_lat + delta_lat
        new_lon = start_lon + delta_lon
        distance = math.sqrt(east_km**2 + north_km**2)
        
        return new_lat, new_lon, distance
