import math
from datetime import datetime

class PowerModel:
    """
    Simulates the energy balance of a stratospheric platform.
    """

    SOLAR_CONSTANT = 1361.0 # W/m^2 (Top of Atmosphere)
    PANEL_EFFICIENCY = 0.22 # 22% efficiency
    SYSTEM_EFFICIENCY = 0.85 # MPPT and battery round-trip losses

    @staticmethod
    def calculate_day_night_hours(lat: float, day_of_year: int) -> tuple[float, float]:
        """
        Calculates day and night hours for a given latitude and day of year.
        Uses a simplified astronomical model.
        """
        # Declination of the sun
        declination = 23.44 * math.sin(math.radians((360 / 365) * (day_of_year - 81)))
        
        # Hour angle at sunrise/sunset
        # cos(h) = -tan(lat) * tan(decl)
        try:
            val = -math.tan(math.radians(lat)) * math.tan(math.radians(declination))
            val = max(-1.0, min(1.0, val)) # Clamp for polar regions
            hour_angle = math.degrees(math.acos(val))
            day_hours = (2 * hour_angle) / 15.0
        except Exception:
            # Fallback for extreme latitudes in extreme seasons (polar day/night)
            if lat * declination > 0:
                day_hours = 24.0 # Polar day
            else:
                day_hours = 0.0 # Polar night
        
        night_hours = 24.0 - day_hours
        return day_hours, night_hours

    @staticmethod
    def check_feasibility(
        lat: float, 
        month: int,
        platform_power_bonus: float, # W (Power provided by platform for payload)
        battery_capacity_wh: float,
        payload_power_w: float
    ) -> dict:
        """
        Determines if the mission is power-positive.
        Simulates the 'worst case' night duration for that month.
        """
        # Approximate day of year from month (mid-month)
        day_of_year = int((month - 1) * 30.5 + 15)
        
        day_hours, night_hours = PowerModel.calculate_day_night_hours(lat, day_of_year)
        
        # Energy required during night
        # Payload runs 24/7 usually, unless duty-cycled. Assuming 100% duty cycle for safety.
        night_energy_needed_wh = payload_power_w * night_hours
        
        # Energy available in battery (Assuming fully charged at sunset)
        # We enforce a safety depth-of-discharge (DoD) of 80% to prolong life
        max_usable_battery_wh = battery_capacity_wh * 0.8
        
        # Check if battery survives the night
        survives_night = max_usable_battery_wh >= night_energy_needed_wh
        
        # Margin
        margin_wh = max_usable_battery_wh - night_energy_needed_wh
        
        return {
            "survives_night": survives_night,
            "day_hours": round(day_hours, 2),
            "night_hours": round(night_hours, 2),
            "night_energy_needed_wh": round(night_energy_needed_wh, 2),
            "battery_capacity_wh": battery_capacity_wh,
            "margin_wh": round(margin_wh, 2),
            "status": "Power Positive" if survives_night else "Insufficient Battery"
        }
