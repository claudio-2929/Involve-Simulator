import random
import math

class FlightModel:
    """
    Simulates wind patterns and station-keeping capability based on Loon library concepts.
    Implements ACS (Altitude Control System) logic where balloons change altitude to find favorable winds.
    """

    # Maximum horizontal correction speed achievable via ACS (km/h)
    STANDARD_ACS_CORRECTION_SPEED = 15.0  # km/h (altitude maneuvers for wind seeking)
    STRATOLLITE_ACS_CORRECTION_SPEED = 25.0  # km/h (enhanced with ballast control)

    @staticmethod
    def calculate_wind_volatility(lat: float, month: int) -> float:
        """
        Returns a volatility score (0.0 to 1.0) based on latitude and season.
        High Lats + Winter = High Volatility (Polar Vortex edge).
        Equator = Low Volatility (QBO phases, but generally calmer).
        """
        # Seasonality: Winter months (NH: Dec-Feb, SH: Jun-Aug) have higher winds.
        is_northern_hemisphere = lat > 0
        if is_northern_hemisphere:
            is_winter = month in [12, 1, 2]
        else:
            is_winter = month in [6, 7, 8]
        
        abs_lat = abs(lat)
        
        base_volatility = 0.1
        
        # Latitude factor: Higher volatility at mid-high latitudes
        lat_factor = 0.0
        if 20 < abs_lat < 60: 
            lat_factor = 0.4
        elif abs_lat >= 60:
            lat_factor = 0.3 # Polar region can be stable inside vortex, but edge is rough.
            
        # Seasonal multiplier
        season_multiplier = 1.5 if is_winter else 1.0
        
        volatility = (base_volatility + lat_factor) * season_multiplier
        return min(0.9, volatility)

    @staticmethod
    def estimate_mean_wind_speed(lat: float, month: int) -> float:
        """
        Estimates mean wind speed at stratospheric altitude (18-25km) in km/h.
        Based on simplified climatology.
        """
        volatility = FlightModel.calculate_wind_volatility(lat, month)
        # Map volatility to wind speed: 0.1 -> 10 km/h, 0.9 -> 50 km/h
        return 10.0 + (volatility * 45.0)

    @staticmethod
    def simulate_station_keeping(
        lat: float, 
        month: int,
        target_radius_km: float,
        platform_type: str = "Super-Pressure"
    ) -> dict:
        """
        Calculates the probability of maintaining position within target_radius_km.
        Returns the Overprovisioning Factor (K) and Drift Warning.
        """
        volatility = FlightModel.calculate_wind_volatility(lat, month)
        mean_wind_speed = FlightModel.estimate_mean_wind_speed(lat, month)
        
        # Select ACS correction speed based on platform type
        if "Zero-Pressure" in platform_type or "Stratollite" in platform_type:
            acs_correction_speed = FlightModel.STRATOLLITE_ACS_CORRECTION_SPEED
        else:
            acs_correction_speed = FlightModel.STANDARD_ACS_CORRECTION_SPEED
        
        # Drift warning: If mean wind exceeds ACS capability
        drift_warning = mean_wind_speed > acs_correction_speed
        drift_excess_ratio = max(0, (mean_wind_speed - acs_correction_speed) / acs_correction_speed)
        
        # Effective volatility adjusted by platform capability
        maneuverability = acs_correction_speed / FlightModel.STANDARD_ACS_CORRECTION_SPEED
        effective_volatility = volatility / maneuverability
        
        # Probability of staying in box (Simulated)
        # Tighter radius = harder to stay.
        radius_difficulty = 50.0 / max(10.0, target_radius_km) # Ref 50km is standard easy box
        
        failure_prob = effective_volatility * radius_difficulty
        failure_prob = min(0.8, max(0.01, failure_prob))
        
        success_prob = 1.0 - failure_prob
        
        # Overprovisioning Factor (K)
        # K = 1 + (failure_prob * 1.5) + drift penalty
        k_factor = 1.0 + (failure_prob * 1.5) + (drift_excess_ratio * 0.5)
        
        # Determine risk level
        if drift_warning:
            drift_risk = "Critical"
        elif failure_prob > 0.4:
            drift_risk = "High"
        elif failure_prob > 0.2:
            drift_risk = "Moderate"
        else:
            drift_risk = "Low"
        
        return {
            "wind_volatility_score": round(volatility, 2),
            "mean_wind_speed_kmh": round(mean_wind_speed, 1),
            "acs_correction_speed_kmh": round(acs_correction_speed, 1),
            "station_keeping_prob": round(success_prob, 2),
            "overprovisioning_factor": round(k_factor, 2),
            "drift_warning": drift_warning,
            "drift_risk": drift_risk,
            "fleet_size_recommended": math.ceil(k_factor)
        }
