import random
import math

class FlightModel:
    """
    Simulates wind patterns and station-keeping capability based on Loon library concepts.
    """

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
    def simulate_station_keeping(
        lat: float, 
        month: int,
        target_radius_km: float,
        platform_maneuverability: float = 1.0 # 1.0 = Standard Loon ACS
    ) -> dict:
        """
        Calculates the probability of maintaining position within target_radius_km.
        Returns the Overprovisioning Factor (K).
        """
        volatility = FlightModel.calculate_wind_volatility(lat, month)
        
        # Manueverability dampens volatility.
        # Loon ACS allows altitude changes to find favorable winds.
        effective_volatility = volatility / platform_maneuverability
        
        # Probability of staying in box (Simulated)
        # Tighter radius = harder to stay.
        radius_difficulty = 50.0 / max(10.0, target_radius_km) # Ref 50km is standard easy box
        
        failure_prob = effective_volatility * radius_difficulty
        failure_prob = min(0.8, max(0.01, failure_prob))
        
        success_prob = 1.0 - failure_prob
        
        # Overprovisioning Factor (K)
        # If success is 50%, you need 2 balloons to ensure 1 is always there on average?
        # Loon approach: "Fleet Replenishment Rate".
        # Simplified: K = 1 + (failure_prob * 2) 
        # e.g. 10% fail -> 1.2x fleet. 50% fail -> 2.0x fleet.
        
        k_factor = 1.0 + (failure_prob * 1.5)
        
        return {
            "wind_volatility_score": round(volatility, 2),
            "station_keeping_prob": round(success_prob, 2),
            "overprovisioning_factor": round(k_factor, 2),
            "drift_risk": "High" if failure_prob > 0.4 else "Moderate" if failure_prob > 0.2 else "Low"
        }
