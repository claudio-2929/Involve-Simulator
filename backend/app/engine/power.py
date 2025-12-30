import math
from datetime import datetime

class PowerModel:
    """
    Simulates the energy balance of a stratospheric platform.
    Now includes Duty Cycle calculation for night operations.
    """

    SOLAR_CONSTANT = 1361.0 # W/m^2 (Top of Atmosphere)
    PANEL_EFFICIENCY = 0.22 # 22% efficiency
    SYSTEM_EFFICIENCY = 0.85 # MPPT and battery round-trip losses
    AVIONICS_POWER = 15.0 # Fixed platform avionics overhead (W)

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
        platform_night_power: float, # W (Power available at night from battery)
        battery_capacity_wh: float,
        payload_power_w: float
    ) -> dict:
        """
        Determines if the mission is power-positive.
        Calculates the achievable duty cycle if power is constrained.
        """
        # Approximate day of year from month (mid-month)
        day_of_year = int((month - 1) * 30.5 + 15)
        
        day_hours, night_hours = PowerModel.calculate_day_night_hours(lat, day_of_year)
        
        # Total power required (payload + avionics)
        total_night_power_required = payload_power_w + PowerModel.AVIONICS_POWER
        
        # Energy required during night (assuming 100% duty cycle)
        night_energy_needed_wh = total_night_power_required * night_hours
        
        # Energy available in battery (80% DoD safety margin)
        max_usable_battery_wh = battery_capacity_wh * 0.8
        
        # Check if platform night power supports payload
        power_sufficient = platform_night_power >= total_night_power_required
        battery_sufficient = max_usable_battery_wh >= night_energy_needed_wh
        
        survives_night = power_sufficient and battery_sufficient
        
        # Calculate achievable duty cycle
        if not power_sufficient:
            # If platform can't power payload, calculate reduced duty cycle
            available_for_payload = max(0, platform_night_power - PowerModel.AVIONICS_POWER)
            duty_cycle = (available_for_payload / payload_power_w) * 100 if payload_power_w > 0 else 0
        elif not battery_sufficient:
            # If battery can't last the night, calculate reduced hours
            achievable_hours = max_usable_battery_wh / total_night_power_required
            duty_cycle = (achievable_hours / night_hours) * 100 if night_hours > 0 else 100
        else:
            duty_cycle = 100.0
        
        duty_cycle = min(100.0, max(0.0, duty_cycle))
        
        # Determine feasibility status
        if duty_cycle >= 80:
            status = "Power Positive"
            is_feasible = True
        elif duty_cycle >= 50:
            status = "Reduced Duty Cycle"
            is_feasible = True
        else:
            status = "Critical Power Shortage"
            is_feasible = False
        
        return {
            "is_feasible": is_feasible,
            "survives_night": survives_night,
            "duty_cycle_percent": round(duty_cycle, 1),
            "day_hours": round(day_hours, 2),
            "night_hours": round(night_hours, 2),
            "night_energy_needed_wh": round(night_energy_needed_wh, 2),
            "battery_capacity_wh": battery_capacity_wh,
            "margin_wh": round(max_usable_battery_wh - night_energy_needed_wh, 2),
            "status": status
        }
