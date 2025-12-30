"""
Monte Carlo Simulation Module - Risk Assessment

Runs multiple scenario simulations to provide:
- Service Reliability: % of time target is covered within quality parameters
- Launch Risk: Probability of launch abort due to surface winds
- Confidence Intervals: Statistical bounds on mission outcomes

Based on understanding that quotes should NOT be based on best-case scenarios.
Simulates winter vs summer, different wind patterns, and operational risks.
"""

import math
import random
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
from .wind import WindField
from .navigator import Navigator
from .fleet import FleetOrchestrator
from .payload_physics import SensorGeometry


@dataclass
class MonteCarloResult:
    """Results from Monte Carlo simulation."""
    n_iterations: int
    service_reliability_percent: float
    service_reliability_std: float
    service_reliability_p5: float  # 5th percentile (worst case)
    service_reliability_p95: float  # 95th percentile (best case)
    expected_drift_events: float
    expected_drift_events_std: float
    launch_abort_probability: float
    recommended_overprovisioning: float
    mission_feasibility: str
    risk_level: str
    confidence_level: str


@dataclass
class ScenarioResult:
    """Single scenario simulation result."""
    service_availability: float
    drift_events: int
    coverage_percent: float
    energy_used_wh: float
    launch_success: bool


class MonteCarloSimulator:
    """
    Multi-scenario risk assessment for mission planning.
    
    Runs N_ITERATIONS simulations with varying conditions:
    - Wind pattern variations
    - Seasonal extremes
    - Surface wind launch conditions
    """
    
    # Simulation parameters
    DEFAULT_ITERATIONS = 50  # Reduced for performance, increase for production
    
    # Surface wind limits for launch
    MAX_LAUNCH_SURFACE_WIND_MS = 8.0  # m/s
    SURFACE_WIND_PROBABILITY_MAP = {
        # Month: (mean_surface_wind_ms, std_dev)
        1: (6.0, 2.5),   # January: windy
        2: (5.5, 2.3),
        3: (5.0, 2.0),
        4: (4.5, 1.8),
        5: (4.0, 1.5),
        6: (3.5, 1.2),   # June: calm
        7: (3.5, 1.2),
        8: (3.8, 1.3),
        9: (4.2, 1.5),
        10: (5.0, 2.0),
        11: (5.5, 2.3),
        12: (6.0, 2.5),  # December: windy
    }
    
    @classmethod
    def run_simulation(
        cls,
        lat: float,
        lon: float,
        aoi_radius_km: float,
        mission_days: int,
        month: int,
        platform_min_alt: float = 18.0,
        platform_max_alt: float = 25.0,
        payload_gsd_m: float = 1.0,
        payload_fov_deg: float = 20.0,
        n_iterations: int = None
    ) -> MonteCarloResult:
        """
        Run Monte Carlo simulation for mission risk assessment.
        
        Args:
            lat, lon: Target AOI center
            aoi_radius_km: AOI radius
            mission_days: Mission duration
            month: Primary month of operation
            platform_min_alt, platform_max_alt: Altitude limits
            payload_gsd_m: Payload GSD specification
            payload_fov_deg: Payload FOV
            n_iterations: Number of simulation runs
            
        Returns:
            MonteCarloResult with statistical outcomes
        """
        iterations = n_iterations or cls.DEFAULT_ITERATIONS
        results: List[ScenarioResult] = []
        
        for i in range(iterations):
            # Vary conditions for each iteration
            scenario_result = cls._run_single_scenario(
                lat=lat,
                lon=lon,
                aoi_radius_km=aoi_radius_km,
                mission_days=mission_days,
                month=month,
                platform_min_alt=platform_min_alt,
                platform_max_alt=platform_max_alt,
                iteration=i
            )
            results.append(scenario_result)
        
        # Calculate statistics
        reliabilities = [r.service_availability for r in results]
        drift_events = [r.drift_events for r in results]
        launch_successes = [1 if r.launch_success else 0 for r in results]
        
        mean_reliability = sum(reliabilities) / len(reliabilities)
        std_reliability = cls._std_dev(reliabilities)
        
        mean_drifts = sum(drift_events) / len(drift_events)
        std_drifts = cls._std_dev([float(d) for d in drift_events])
        
        launch_abort_prob = 1.0 - (sum(launch_successes) / len(launch_successes))
        
        # Percentiles
        sorted_rel = sorted(reliabilities)
        p5_idx = max(0, int(len(sorted_rel) * 0.05))
        p95_idx = min(len(sorted_rel) - 1, int(len(sorted_rel) * 0.95))
        
        # Determine risk level
        risk_level = cls._assess_risk_level(mean_reliability, std_reliability, launch_abort_prob)
        
        # Determine feasibility
        feasibility = cls._assess_feasibility(mean_reliability, launch_abort_prob)
        
        # Calculate recommended overprovisioning based on variance
        # Higher variance = more overprovisioning needed
        overprov = 1.0 + (std_reliability / 50) + (mean_drifts / (mission_days * 2))
        
        return MonteCarloResult(
            n_iterations=iterations,
            service_reliability_percent=round(mean_reliability, 1),
            service_reliability_std=round(std_reliability, 2),
            service_reliability_p5=round(sorted_rel[p5_idx], 1),
            service_reliability_p95=round(sorted_rel[p95_idx], 1),
            expected_drift_events=round(mean_drifts, 1),
            expected_drift_events_std=round(std_drifts, 2),
            launch_abort_probability=round(launch_abort_prob * 100, 1),
            recommended_overprovisioning=round(max(1.0, overprov), 2),
            mission_feasibility=feasibility,
            risk_level=risk_level,
            confidence_level="High" if iterations >= 50 else "Medium" if iterations >= 20 else "Low"
        )
    
    @classmethod
    def _run_single_scenario(
        cls,
        lat: float,
        lon: float,
        aoi_radius_km: float,
        mission_days: int,
        month: int,
        platform_min_alt: float,
        platform_max_alt: float,
        iteration: int
    ) -> ScenarioResult:
        """Run a single scenario with random variation."""
        
        # Check launch conditions
        launch_success = cls._simulate_launch_conditions(lat, month)
        
        if not launch_success:
            return ScenarioResult(
                service_availability=0,
                drift_events=0,
                coverage_percent=0,
                energy_used_wh=0,
                launch_success=False
            )
        
        # Run station-keeping simulation with time limit for performance
        sim_hours = min(mission_days * 24, 168)  # Max 1 week simulation
        
        result = Navigator.simulate_station_keeping(
            start_lat=lat,
            start_lon=lon,
            target_lat=lat,
            target_lon=lon,
            aoi_radius_km=aoi_radius_km,
            mission_hours=sim_hours,
            month=month,
            platform_min_alt=platform_min_alt,
            platform_max_alt=platform_max_alt,
            initial_altitude_km=(platform_min_alt + platform_max_alt) / 2,
            time_step_hours=2.0  # Coarser time step for performance
        )
        
        return ScenarioResult(
            service_availability=result.coverage_percent,
            drift_events=result.drift_events,
            coverage_percent=result.coverage_percent,
            energy_used_wh=result.total_energy_used_wh,
            launch_success=True
        )
    
    @classmethod
    def _simulate_launch_conditions(cls, lat: float, month: int) -> bool:
        """Simulate whether launch conditions are acceptable."""
        mean_wind, std_wind = cls.SURFACE_WIND_PROBABILITY_MAP.get(month, (5.0, 2.0))
        
        # Latitude affects surface winds (higher = more variable)
        lat_factor = 1.0 + abs(lat) / 90 * 0.3
        
        # Sample surface wind speed
        surface_wind = random.gauss(mean_wind * lat_factor, std_wind)
        
        return surface_wind <= cls.MAX_LAUNCH_SURFACE_WIND_MS
    
    @classmethod
    def _assess_risk_level(
        cls,
        mean_reliability: float,
        std_reliability: float,
        launch_abort_prob: float
    ) -> str:
        """Assess overall mission risk level."""
        # Risk score: lower reliability, higher variance, higher abort = more risk
        risk_score = (100 - mean_reliability) + (std_reliability * 2) + (launch_abort_prob * 100)
        
        if risk_score < 30:
            return "Low"
        elif risk_score < 60:
            return "Medium"
        elif risk_score < 90:
            return "High"
        else:
            return "Critical"
    
    @classmethod
    def _assess_feasibility(
        cls,
        mean_reliability: float,
        launch_abort_prob: float
    ) -> str:
        """Assess overall mission feasibility."""
        if mean_reliability >= 80 and launch_abort_prob < 0.3:
            return "Highly Feasible"
        elif mean_reliability >= 60 and launch_abort_prob < 0.5:
            return "Feasible"
        elif mean_reliability >= 40:
            return "Marginal"
        else:
            return "Not Recommended"
    
    @staticmethod
    def _std_dev(values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)
    
    @classmethod
    def get_seasonal_comparison(
        cls,
        lat: float,
        lon: float,
        aoi_radius_km: float,
        mission_days: int
    ) -> Dict[str, MonteCarloResult]:
        """
        Compare mission outcomes across seasons.
        
        Returns results for winter and summer scenarios.
        """
        is_northern = lat > 0
        
        # Define seasonal months
        winter_month = 1 if is_northern else 7
        summer_month = 7 if is_northern else 1
        
        winter_result = cls.run_simulation(
            lat, lon, aoi_radius_km, mission_days,
            month=winter_month, n_iterations=30
        )
        
        summer_result = cls.run_simulation(
            lat, lon, aoi_radius_km, mission_days,
            month=summer_month, n_iterations=30
        )
        
        return {
            "winter": winter_result,
            "summer": summer_result
        }
