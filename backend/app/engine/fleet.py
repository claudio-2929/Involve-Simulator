"""
Fleet Orchestration Module - Multi-Platform Coverage Management

Based on Project Loon's fleet management concepts:
- Multiple platforms ensure continuous service coverage
- "Leaky Bucket" model: platforms drift out, replacements launched
- Overprovisioning factor accounts for drift and replacement scheduling

Key metrics:
- Revisit Time: How often can we image a target
- Overprovisioning Factor: How many platforms needed for 1 "always-on" equivalent
- Service Availability: % of time target is covered
"""

import math
from typing import Dict, List, Tuple
from dataclasses import dataclass
from .navigator import Navigator, StationKeepingResult


@dataclass
class RevisitMetrics:
    """Metrics for target revisit capability."""
    revisit_time_hours: float
    coverage_gaps_per_day: float
    max_gap_duration_hours: float
    average_gap_duration_hours: float


@dataclass
class FleetSimulationResult:
    """Result of fleet-level simulation."""
    n_platforms: int
    overprovisioning_factor: float
    service_availability_percent: float
    average_revisit_hours: float
    total_drift_events: int
    replacement_launches_needed: int
    total_mission_cost_multiplier: float


class FleetOrchestrator:
    """
    Fleet-level coverage and replacement management.
    
    Calculates how many platforms are needed to maintain
    continuous coverage, accounting for drift events and
    replacement scheduling.
    """
    
    # Fleet management parameters
    REPLACEMENT_LEAD_TIME_HOURS = 24  # Launch new platform 24h before drift
    MIN_OVERLAP_HOURS = 4  # Minimum overlap between platforms
    
    @classmethod
    def calculate_revisit_time(
        cls,
        aoi_area_km2: float,
        swath_width_km: float,
        ground_speed_kmh: float,
        n_platforms: int,
        off_nadir_capability_deg: float = 0
    ) -> RevisitMetrics:
        """
        Calculate how often a point in the AOI can be imaged.
        
        Formula: RevisitTime = AOI_Area / (SwathWidth × GroundSpeed × N_Platforms)
        
        Args:
            aoi_area_km2: Area of Interest in km²
            swath_width_km: Sensor swath width at operating altitude
            ground_speed_kmh: Platform ground speed (from wind)
            n_platforms: Number of platforms in fleet
            off_nadir_capability_deg: Off-nadir pointing capability
            
        Returns:
            RevisitMetrics with timing analysis
        """
        # Effective swath increases with off-nadir capability
        # At 30° off-nadir, effective width ≈ 1.4x nadir swath
        off_nadir_factor = 1.0 + (off_nadir_capability_deg / 60.0)
        effective_swath = swath_width_km * off_nadir_factor
        
        # Coverage rate in km²/hour
        coverage_rate = effective_swath * ground_speed_kmh * max(1, n_platforms)
        
        # Time to cover entire AOI
        if coverage_rate > 0:
            revisit_time = aoi_area_km2 / coverage_rate
        else:
            revisit_time = float('inf')
        
        # Estimate gaps (simplified model)
        # Higher wind = faster movement = more gaps in figure-8 pattern
        gaps_per_day = max(0, 24 / revisit_time - n_platforms) if revisit_time < 24 else 0
        
        return RevisitMetrics(
            revisit_time_hours=round(revisit_time, 2),
            coverage_gaps_per_day=round(gaps_per_day, 1),
            max_gap_duration_hours=round(revisit_time / max(1, n_platforms), 2),
            average_gap_duration_hours=round(revisit_time / max(1, n_platforms * 2), 2)
        )
    
    @classmethod
    def calculate_overprovisioning_factor(
        cls,
        drift_probability_per_day: float,
        mission_days: int,
        target_availability: float = 0.95
    ) -> float:
        """
        Calculate fleet overprovisioning factor.
        
        Based on Loon's "Leaky Bucket" model:
        - Platforms drift out with some probability
        - Need extra platforms to maintain coverage
        
        Args:
            drift_probability_per_day: Probability of drift event per day
            mission_days: Total mission duration
            target_availability: Desired service availability (0-1)
            
        Returns:
            Overprovisioning factor (e.g., 1.4 means need 1.4 platforms for 1 effective)
        """
        # Expected drift events over mission
        expected_drifts = drift_probability_per_day * mission_days
        
        # Availability with N platforms: A = 1 - (drift_events / N)
        # Solving for N to achieve target availability:
        # N = expected_drifts / (1 - target_availability)
        
        required_multiple = 1 + (drift_probability_per_day / (1 - target_availability))
        
        # Add safety buffer for replacement scheduling
        scheduling_buffer = 1.0 + (cls.REPLACEMENT_LEAD_TIME_HOURS / (mission_days * 24))
        
        factor = required_multiple * scheduling_buffer
        
        return round(max(1.0, factor), 2)
    
    @classmethod
    def simulate_fleet_coverage(
        cls,
        target_lat: float,
        target_lon: float,
        aoi_radius_km: float,
        mission_days: int,
        month: int,
        n_platforms: int = 1,
        platform_min_alt: float = 18.0,
        platform_max_alt: float = 25.0
    ) -> FleetSimulationResult:
        """
        Simulate fleet-level coverage over mission duration.
        
        Runs individual platform simulations and aggregates results
        to determine overall service availability.
        
        Args:
            target_lat, target_lon: AOI center
            aoi_radius_km: AOI radius
            mission_days: Mission duration in days
            month: Month for wind patterns
            n_platforms: Number of platforms to simulate
            platform_min_alt, platform_max_alt: Altitude limits
            
        Returns:
            FleetSimulationResult with coverage analysis
        """
        mission_hours = mission_days * 24
        total_drift_events = 0
        total_time_on_target = 0.0
        
        # Simulate each platform
        for i in range(max(1, n_platforms)):
            # Stagger platform positions slightly
            offset_angle = (360 / max(1, n_platforms)) * i
            offset_rad = math.radians(offset_angle)
            start_lat = target_lat + (aoi_radius_km * 0.5 / 111) * math.cos(offset_rad)
            start_lon = target_lon + (aoi_radius_km * 0.5 / 111) * math.sin(offset_rad)
            
            result = Navigator.simulate_station_keeping(
                start_lat=start_lat,
                start_lon=start_lon,
                target_lat=target_lat,
                target_lon=target_lon,
                aoi_radius_km=aoi_radius_km,
                mission_hours=mission_hours,
                month=month,
                platform_min_alt=platform_min_alt,
                platform_max_alt=platform_max_alt,
                initial_altitude_km=(platform_min_alt + platform_max_alt) / 2
            )
            
            total_drift_events += result.drift_events
            total_time_on_target += result.time_on_target_hours
        
        # Calculate aggregate metrics
        service_availability = (total_time_on_target / (mission_hours * n_platforms)) * 100
        
        # Drift probability per day (empirical from simulation)
        drift_per_day = total_drift_events / (mission_days * n_platforms) if mission_days > 0 else 0
        
        # Calculate overprovisioning for 95% availability
        overprov_factor = cls.calculate_overprovisioning_factor(
            drift_per_day, mission_days, target_availability=0.95
        )
        
        # Replacement launches needed
        replacements_needed = math.ceil(total_drift_events / max(1, n_platforms))
        
        return FleetSimulationResult(
            n_platforms=n_platforms,
            overprovisioning_factor=overprov_factor,
            service_availability_percent=round(service_availability, 1),
            average_revisit_hours=24 / max(1, n_platforms),  # Simplified
            total_drift_events=total_drift_events,
            replacement_launches_needed=replacements_needed,
            total_mission_cost_multiplier=overprov_factor
        )
    
    @classmethod
    def recommend_fleet_size(
        cls,
        target_lat: float,
        target_lon: float,
        aoi_radius_km: float,
        mission_days: int,
        month: int,
        target_availability: float = 0.95,
        max_platforms: int = 5
    ) -> Dict:
        """
        Recommend optimal fleet size for target availability.
        
        Runs simulations with increasing fleet sizes until
        target availability is met.
        
        Args:
            target_lat, target_lon: AOI center
            aoi_radius_km: AOI radius
            mission_days: Mission duration
            month: Month for wind patterns
            target_availability: Required availability (0-1)
            max_platforms: Maximum platforms to consider
            
        Returns:
            Recommendation with fleet size and metrics
        """
        best_result = None
        
        for n in range(1, max_platforms + 1):
            result = cls.simulate_fleet_coverage(
                target_lat, target_lon, aoi_radius_km,
                mission_days, month, n_platforms=n
            )
            
            if result.service_availability_percent >= target_availability * 100:
                best_result = result
                break
            
            best_result = result  # Keep last result if target not met
        
        return {
            "recommended_fleet_size": best_result.n_platforms if best_result else 1,
            "expected_availability_percent": best_result.service_availability_percent if best_result else 0,
            "overprovisioning_factor": best_result.overprovisioning_factor if best_result else 1.0,
            "meets_target": (best_result.service_availability_percent >= target_availability * 100) if best_result else False,
            "simulation_details": best_result
        }
