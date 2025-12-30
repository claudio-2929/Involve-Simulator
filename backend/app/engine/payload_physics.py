"""
Payload Physics Module - Altitude-Dependent Sensor Performance

Calculates imaging performance based on:
- Altitude: Higher = wider swath but lower resolution (larger GSD)
- Off-Nadir angle: Sideways pointing extends coverage but degrades quality
- FOV: Wider field of view = more coverage per pass

Key relationships:
- GSD scales linearly with altitude: GSD = base_gsd × (current_alt / base_alt)
- Swath = 2 × altitude × tan(FOV/2)
- Off-nadir quality factor = cos(off_nadir_angle)
"""

import math
from typing import Dict, Tuple
from dataclasses import dataclass


@dataclass
class ImagingPerformance:
    """Imaging performance at specific conditions."""
    gsd_m: float  # Ground Sample Distance in meters
    swath_width_km: float  # Swath width in km
    coverage_rate_km2_h: float  # km² per hour
    quality_factor: float  # 0-1, 1 = perfect
    altitude_km: float
    off_nadir_deg: float


@dataclass
class CoverageAnalysis:
    """Analysis of coverage capability."""
    effective_gsd_m: float
    min_gsd_m: float  # At lowest altitude
    max_gsd_m: float  # At highest altitude
    average_swath_km: float
    repositioning_coverage_loss_percent: float
    effective_coverage_percent: float


class SensorGeometry:
    """
    Calculate altitude-dependent sensor imaging performance.
    
    Models how GSD and swath change as the platform maneuvers
    to different altitudes for station-keeping.
    """
    
    # Standard reference altitude for sensor specs (km)
    REFERENCE_ALTITUDE_KM = 20.0
    
    # Off-nadir limits
    MAX_OFF_NADIR_DEG = 45.0
    
    @classmethod
    def calculate_gsd(
        cls,
        base_gsd_m: float,
        base_altitude_km: float,
        current_altitude_km: float
    ) -> float:
        """
        Calculate GSD at current altitude.
        
        GSD scales linearly with altitude:
        GSD = base_gsd × (current_altitude / base_altitude)
        
        Args:
            base_gsd_m: Specified GSD at base altitude
            base_altitude_km: Altitude at which GSD is specified
            current_altitude_km: Current operating altitude
            
        Returns:
            GSD in meters at current altitude
        """
        if base_altitude_km <= 0:
            base_altitude_km = cls.REFERENCE_ALTITUDE_KM
        
        scaling_factor = current_altitude_km / base_altitude_km
        return round(base_gsd_m * scaling_factor, 3)
    
    @classmethod
    def calculate_swath(
        cls,
        fov_deg: float,
        altitude_km: float,
        off_nadir_deg: float = 0
    ) -> float:
        """
        Calculate swath width at given altitude and pointing angle.
        
        Swath = 2 × altitude × tan(FOV/2)
        
        Off-nadir pointing increases effective swath but at quality cost.
        
        Args:
            fov_deg: Field of view in degrees
            altitude_km: Operating altitude in km
            off_nadir_deg: Off-nadir pointing angle
            
        Returns:
            Swath width in km
        """
        # Base swath from FOV and altitude
        half_fov_rad = math.radians(fov_deg / 2)
        base_swath_km = 2 * altitude_km * math.tan(half_fov_rad)
        
        # Off-nadir extends effective coverage
        # At 30° off-nadir, we can see further to the side
        off_nadir_extension = 1.0 + (off_nadir_deg / 90.0) * 0.5
        
        return round(base_swath_km * off_nadir_extension, 2)
    
    @classmethod
    def calculate_quality_factor(cls, off_nadir_deg: float) -> float:
        """
        Calculate image quality degradation from off-nadir viewing.
        
        Quality = cos(off_nadir_angle)
        At nadir (0°): quality = 1.0
        At 45°: quality ≈ 0.7
        
        Args:
            off_nadir_deg: Off-nadir angle in degrees
            
        Returns:
            Quality factor 0-1
        """
        angle_rad = math.radians(min(abs(off_nadir_deg), 60))
        return round(math.cos(angle_rad), 2)
    
    @classmethod
    def calculate_imaging_performance(
        cls,
        base_gsd_m: float,
        fov_deg: float,
        altitude_km: float,
        ground_speed_kmh: float,
        off_nadir_deg: float = 0
    ) -> ImagingPerformance:
        """
        Calculate complete imaging performance at given conditions.
        
        Args:
            base_gsd_m: Base GSD at reference altitude
            fov_deg: Sensor FOV
            altitude_km: Current altitude
            ground_speed_kmh: Platform ground speed
            off_nadir_deg: Off-nadir angle
            
        Returns:
            ImagingPerformance with all metrics
        """
        gsd = cls.calculate_gsd(base_gsd_m, cls.REFERENCE_ALTITUDE_KM, altitude_km)
        swath = cls.calculate_swath(fov_deg, altitude_km, off_nadir_deg)
        quality = cls.calculate_quality_factor(off_nadir_deg)
        
        # Coverage rate: area covered per hour
        coverage_rate = swath * ground_speed_kmh
        
        return ImagingPerformance(
            gsd_m=gsd,
            swath_width_km=swath,
            coverage_rate_km2_h=round(coverage_rate, 1),
            quality_factor=quality,
            altitude_km=altitude_km,
            off_nadir_deg=off_nadir_deg
        )
    
    @classmethod
    def analyze_mission_coverage(
        cls,
        base_gsd_m: float,
        fov_deg: float,
        min_altitude_km: float,
        max_altitude_km: float,
        average_ground_speed_kmh: float,
        station_keeping_coverage_percent: float
    ) -> CoverageAnalysis:
        """
        Analyze overall mission coverage considering altitude variations.
        
        During station-keeping, the platform changes altitude to find
        favorable winds. This affects imaging performance.
        
        Args:
            base_gsd_m: Base GSD specification
            fov_deg: Sensor FOV
            min_altitude_km, max_altitude_km: Operating altitude range
            average_ground_speed_kmh: Average wind-driven speed
            station_keeping_coverage_percent: % time on target (from Navigator)
            
        Returns:
            CoverageAnalysis with mission-level metrics
        """
        # GSD range
        gsd_at_min = cls.calculate_gsd(base_gsd_m, cls.REFERENCE_ALTITUDE_KM, min_altitude_km)
        gsd_at_max = cls.calculate_gsd(base_gsd_m, cls.REFERENCE_ALTITUDE_KM, max_altitude_km)
        avg_altitude = (min_altitude_km + max_altitude_km) / 2
        effective_gsd = cls.calculate_gsd(base_gsd_m, cls.REFERENCE_ALTITUDE_KM, avg_altitude)
        
        # Swath at average altitude
        avg_swath = cls.calculate_swath(fov_deg, avg_altitude)
        
        # Repositioning loss: time spent maneuvering instead of imaging
        # Typically 5-15% overhead for altitude changes
        repositioning_loss = 100 - station_keeping_coverage_percent
        
        # Effective coverage considering repositioning losses
        effective_coverage = station_keeping_coverage_percent * 0.95  # 5% imaging overhead
        
        return CoverageAnalysis(
            effective_gsd_m=effective_gsd,
            min_gsd_m=gsd_at_min,
            max_gsd_m=gsd_at_max,
            average_swath_km=avg_swath,
            repositioning_coverage_loss_percent=round(repositioning_loss, 1),
            effective_coverage_percent=round(effective_coverage, 1)
        )
    
    @classmethod
    def calculate_aoi_area(cls, radius_km: float) -> float:
        """Calculate circular AOI area in km²."""
        return math.pi * radius_km ** 2
    
    @classmethod
    def estimate_full_coverage_time(
        cls,
        aoi_radius_km: float,
        swath_width_km: float,
        ground_speed_kmh: float
    ) -> float:
        """
        Estimate time to fully cover AOI once.
        
        Args:
            aoi_radius_km: AOI radius
            swath_width_km: Sensor swath width
            ground_speed_kmh: Platform ground speed
            
        Returns:
            Time in hours to cover AOI
        """
        aoi_area = cls.calculate_aoi_area(aoi_radius_km)
        coverage_rate = swath_width_km * ground_speed_kmh
        
        if coverage_rate > 0:
            return round(aoi_area / coverage_rate, 2)
        return float('inf')
