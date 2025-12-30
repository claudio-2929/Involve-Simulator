from typing import Dict, Any

class PricingEngine:
    """
    Calculates the detailed cost breakdown and final pricing for a mission.
    """

    # Global Assumptions
    LAUNCH_TEAM_DAILY_RATE = 2000.0 # Cost of launch team/ops per day
    DATALINK_COST_PER_GB = 5.0 # $/GB satellite link

    @staticmethod
    def calculate_quote(
        platform: dict, # Pydantic/SQLModel dict
        payload: dict,
        mission_input: dict,
        flight_result: dict, # From FlightModel
        margin_percent: float = 0.30 # 30% default margin
    ) -> Dict[str, Any]:
        
        duration_days = mission_input.get("duration", 30)
        overprovisioning_factor = flight_result.get("overprovisioning_factor", 1.0)
        
        # 1. Platform Costs
        # Amortization per flight = (CAPEX + Launch) / AmortizationFlights
        # But here we might charge based on usage days vs total life?
        # Let's use: (CAPEX / LifetimeDays) * MissionDays
        # Simplified: CAPEX is amortized over a fixed number of flights.
        
        platform_capex = platform["capex"]
        launch_cost = platform["launch_cost"]
        amort_flights = platform.get("amortization_flights", 1)
        
        cost_per_flight_amortized = (platform_capex + launch_cost) / max(1, amort_flights)
        
        # If mission is longer than standard flight? We assume one launch covers the mission duration
        # unless duration > max_duration.
        
        # 2. Payload Costs
        # Payload is reusable. Amortized over N missions (e.g. 10).
        payload_amortization_missions = 10
        payload_cost_per_mission = payload["capex"] / payload_amortization_missions
        
        # 3. Operations Costs (OPEX)
        # Fleet monitoring.
        daily_ops_cost = PricingEngine.LAUNCH_TEAM_DAILY_RATE * overprovisioning_factor
        total_ops_cost = daily_ops_cost * duration_days
        
        # 4. Data Costs
        daily_data_gb = payload.get("daily_data_rate_gb", 0)
        total_data_gb = daily_data_gb * duration_days * overprovisioning_factor
        data_cost = total_data_gb * PricingEngine.DATALINK_COST_PER_GB
        
        # 5. Total Base Cost (One unit)
        base_mission_cost = cost_per_flight_amortized + payload_cost_per_mission
        
        # 6. Apply Overprovisioning (Fleet Multiplier)
        # If we need 1.5 balloons, we pay for 1.5x platforms?
        # Usually implies launching 2 and keeping one as backup or overlapping.
        # We will multiply Platform/Launch costs by K factor.
        
        total_platform_cost = base_mission_cost * overprovisioning_factor
        
        total_cost = total_platform_cost + total_ops_cost + data_cost
        
        # 7. Price
        price = total_cost / (1.0 - margin_percent)
        net_margin = price - total_cost
        
        return {
            "breakdown": {
                "platform_amortized": round(cost_per_flight_amortized * overprovisioning_factor, 2),
                "payload_amortized": round(payload_cost_per_mission * overprovisioning_factor, 2),
                "ops_cost": round(total_ops_cost, 2),
                "data_cost": round(data_cost, 2),
                "overprovisioning_factor": overprovisioning_factor
            },
            "total_cost": round(total_cost, 2),
            "price_quoted": round(price, 2),
            "margin_absolute": round(net_margin, 2),
            "margin_percent": round(margin_percent * 100, 1)
        }
