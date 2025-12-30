"""
Navigator Module - Altitude Control System (ACS) for Station Keeping

Based on Project Loon's ACS (Altitude Control System):
- Platform has NO lateral propulsion, only vertical control
- Navigation is achieved by finding altitude layers with favorable wind
- Changes altitude using ballonets (pump air in/out) or ballast
- Each altitude change costs energy and takes time

Key constraints:
- Max climb rate: 0.5 m/s (limited by pump capacity)
- Max descent rate: 0.8 m/s (controlled venting)
- Altitude change power: 50W continuous during maneuver
"""

import math
from typing import Tuple, Dict, List, Optional
from dataclasses import dataclass
from .wind import WindField, WindVector


@dataclass
class NavigationDecision:
    """Result of a navigation decision."""
    current_altitude_km: float
    target_altitude_km: float
    altitude_change_km: float
    direction: str  # "climb", "descend", "hold"
    time_to_complete_s: float
    energy_cost_wh: float
    expected_drift_km: float
    expected_heading_deg: float
    will_stay_in_aoi: bool
    reasoning: str


@dataclass
class StationKeepingResult:
    """Result of a station-keeping simulation."""
    total_hours: float
    time_on_target_hours: float
    time_repositioning_hours: float
    drift_events: int
    total_energy_used_wh: float
    altitude_changes: int
    coverage_percent: float
    trajectory: List[Dict]


class Navigator:
    """
    Loon-style Altitude Control System (ACS) Navigator.
    
    Implements station-keeping by strategically changing altitude
    to find wind layers that push the platform toward/within the target AOI.
    """
    
    # Physical constraints
    CLIMB_RATE_MS = 0.5      # Max climb speed (m/s)
    DESCENT_RATE_MS = 0.8    # Max descent speed (m/s)
    
    # Power consumption
    ACS_PUMP_POWER_W = 50    # Power used during altitude change
    AVIONICS_POWER_W = 15    # Baseline avionics consumption
    
    # Altitude limits
    MIN_ALTITUDE_KM = 18.0
    MAX_ALTITUDE_KM = 25.0
    
    # Decision thresholds
    LOOKAHEAD_HOURS = 2.0    # How far ahead to predict
    AOI_EXIT_THRESHOLD = 0.8  # Trigger repositioning at 80% of AOI radius
    
    @classmethod
    def decide_altitude_change(
        cls,
        current_lat: float,
        current_lon: float,
        current_altitude_km: float,
        target_lat: float,
        target_lon: float,
        aoi_radius_km: float,
        month: int,
        platform_min_alt: float = 18.0,
        platform_max_alt: float = 25.0
    ) -> NavigationDecision:
        """
        Decide whether to change altitude for better station-keeping.
        
        Uses lookahead algorithm:
        1. For each possible altitude, predict position after LOOKAHEAD_HOURS
        2. Select altitude that keeps platform closest to target
        3. If no altitude works, report drift event
        
        Args:
            current_lat, current_lon: Current platform position
            current_altitude_km: Current altitude
            target_lat, target_lon: Center of AOI
            aoi_radius_km: Radius of Area of Interest
            month: Current month (affects wind patterns)
            platform_min_alt, platform_max_alt: Platform altitude limits
            
        Returns:
            NavigationDecision with recommended action
        """
        # Calculate current distance to target
        current_distance = cls._haversine_distance(
            current_lat, current_lon, target_lat, target_lon
        )
        
        # Calculate heading to target
        target_heading = cls._bearing(
            current_lat, current_lon, target_lat, target_lon
        )
        
        best_altitude = current_altitude_km
        best_distance_after = float('inf')
        best_prediction = None
        
        # Evaluate each altitude option
        altitude_range = (
            max(cls.MIN_ALTITUDE_KM, platform_min_alt),
            min(cls.MAX_ALTITUDE_KM, platform_max_alt)
        )
        
        for alt in [18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0]:
            if altitude_range[0] <= alt <= altitude_range[1]:
                # Predict position after lookahead period at this altitude
                new_lat, new_lon, drift_km = WindField.simulate_drift(
                    current_lat, current_lon, alt,
                    cls.LOOKAHEAD_HOURS, month
                )
                
                # Calculate distance to target after drift
                distance_after = cls._haversine_distance(
                    new_lat, new_lon, target_lat, target_lon
                )
                
                if distance_after < best_distance_after:
                    best_distance_after = distance_after
                    best_altitude = alt
                    best_prediction = (new_lat, new_lon, drift_km)
        
        # Calculate altitude change parameters
        altitude_change = best_altitude - current_altitude_km
        
        if abs(altitude_change) < 0.5:
            # Small change, hold current altitude
            direction = "hold"
            time_to_complete = 0
            energy_cost = 0
        elif altitude_change > 0:
            # Climb
            direction = "climb"
            altitude_change_m = altitude_change * 1000
            time_to_complete = altitude_change_m / cls.CLIMB_RATE_MS
            energy_cost = (cls.ACS_PUMP_POWER_W * time_to_complete) / 3600  # Wh
        else:
            # Descend
            direction = "descend"
            altitude_change_m = abs(altitude_change) * 1000
            time_to_complete = altitude_change_m / cls.DESCENT_RATE_MS
            energy_cost = (cls.ACS_PUMP_POWER_W * time_to_complete) / 3600  # Wh
        
        # Will platform stay in AOI?
        will_stay = best_distance_after <= aoi_radius_km
        
        # Get wind at target altitude for heading info
        wind = WindField.get_wind_vector(
            current_lat, current_lon, best_altitude, month
        )
        travel_heading = (wind.direction_deg + 180) % 360
        
        reasoning = (
            f"Current: {current_altitude_km:.1f}km, dist={current_distance:.1f}km. "
            f"Best: {best_altitude:.1f}km → predicted dist={best_distance_after:.1f}km. "
            f"{'DRIFT EVENT!' if not will_stay else 'OK'}"
        )
        
        return NavigationDecision(
            current_altitude_km=current_altitude_km,
            target_altitude_km=best_altitude,
            altitude_change_km=altitude_change,
            direction=direction,
            time_to_complete_s=time_to_complete,
            energy_cost_wh=round(energy_cost, 2),
            expected_drift_km=best_prediction[2] if best_prediction else 0,
            expected_heading_deg=travel_heading,
            will_stay_in_aoi=will_stay,
            reasoning=reasoning
        )
    
    @classmethod
    def simulate_station_keeping(
        cls,
        start_lat: float,
        start_lon: float,
        target_lat: float,
        target_lon: float,
        aoi_radius_km: float,
        mission_hours: float,
        month: int,
        platform_min_alt: float = 18.0,
        platform_max_alt: float = 25.0,
        initial_altitude_km: float = 20.0,
        time_step_hours: float = 1.0
    ) -> StationKeepingResult:
        """
        Simulate station-keeping over a mission duration.
        
        Runs a time-stepped simulation where the navigator makes
        altitude decisions at each step to maintain position.
        
        Args:
            start_lat, start_lon: Initial platform position
            target_lat, target_lon: AOI center
            aoi_radius_km: AOI radius
            mission_hours: Total mission duration
            month: Month for wind patterns
            platform_min_alt, platform_max_alt: Altitude limits
            initial_altitude_km: Starting altitude
            time_step_hours: Simulation time step
            
        Returns:
            StationKeepingResult with simulation metrics
        """
        current_lat = start_lat
        current_lon = start_lon
        current_alt = initial_altitude_km
        
        total_energy_used = 0.0
        time_on_target = 0.0
        time_repositioning = 0.0
        drift_events = 0
        altitude_changes = 0
        trajectory = []
        
        t = 0.0
        while t < mission_hours:
            # Make navigation decision
            decision = cls.decide_altitude_change(
                current_lat, current_lon, current_alt,
                target_lat, target_lon, aoi_radius_km,
                month, platform_min_alt, platform_max_alt
            )
            
            # Apply altitude change
            if decision.direction != "hold":
                altitude_changes += 1
                total_energy_used += decision.energy_cost_wh
                current_alt = decision.target_altitude_km
            
            # Simulate drift for this time step
            new_lat, new_lon, drift_km = WindField.simulate_drift(
                current_lat, current_lon, current_alt,
                time_step_hours, month
            )
            
            # Calculate distance to target
            distance = cls._haversine_distance(
                new_lat, new_lon, target_lat, target_lon
            )
            
            # Track coverage
            if distance <= aoi_radius_km:
                time_on_target += time_step_hours
            else:
                time_repositioning += time_step_hours
                drift_events += 1
            
            # Add avionics power for this step
            total_energy_used += cls.AVIONICS_POWER_W * time_step_hours
            
            # Record trajectory
            trajectory.append({
                "t_hours": t,
                "lat": round(new_lat, 4),
                "lon": round(new_lon, 4),
                "alt_km": current_alt,
                "distance_km": round(distance, 2),
                "in_aoi": distance <= aoi_radius_km
            })
            
            current_lat = new_lat
            current_lon = new_lon
            t += time_step_hours
        
        coverage_percent = (time_on_target / mission_hours) * 100 if mission_hours > 0 else 0
        
        return StationKeepingResult(
            total_hours=mission_hours,
            time_on_target_hours=round(time_on_target, 2),
            time_repositioning_hours=round(time_repositioning, 2),
            drift_events=drift_events,
            total_energy_used_wh=round(total_energy_used, 2),
            altitude_changes=altitude_changes,
            coverage_percent=round(coverage_percent, 1),
            trajectory=trajectory
        )
    
    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate great-circle distance in km between two points."""
        R = 6371  # Earth's radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    @staticmethod
    def _bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate initial bearing from point 1 to point 2."""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lon = math.radians(lon2 - lon1)
        
        x = math.sin(delta_lon) * math.cos(lat2_rad)
        y = (math.cos(lat1_rad) * math.sin(lat2_rad) -
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon))
        
        bearing = math.atan2(x, y)
        return (math.degrees(bearing) + 360) % 360
