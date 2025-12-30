export interface Platform {
    id: number;
    name: string;
    platform_type: string;
    capex: number;
    launch_cost: number;
    consumables_cost: number;
    max_payload_mass: number;
    min_altitude: number;
    max_altitude: number;
    max_duration_days: number;
    amortization_flights: number;
    day_power: number;
    night_power: number;
    battery_capacity: number;
}

export interface Payload {
    id: number;
    name: string;
    capex: number;
    mass: number;
    power_consumption: number;
    resolution_gsd: number;
    fov: number;
    daily_data_rate_gb: number;
    market: string;
}

export interface SimulationRequest {
    platform_id: number;
    payload_id: number;
    lat: number;
    lon: number;
    month: number;
    duration_days: number;
    target_radius_km: number;
    margin_percent: number;
}

export interface QuoteBreakdown {
    platform_amortized: number;
    payload_amortized: number;
    ops_cost: number;
    data_cost: number;
    overprovisioning_factor: number;
}

export interface SimulationResponse {
    is_feasible: boolean;
    warnings: string[];
    power_analysis: {
        is_feasible: boolean;
        survives_night: boolean;
        duty_cycle_percent: number;
        day_hours: number;
        night_hours: number;
        margin_wh: number;
        status: string;
    };
    flight_analysis: {
        wind_volatility_score: number;
        mean_wind_speed_kmh: number;
        acs_correction_speed_kmh: number;
        station_keeping_prob: number;
        overprovisioning_factor: number;
        drift_warning: boolean;
        drift_risk: string;
        fleet_size_recommended: number;
    };
    quote: {
        breakdown: QuoteBreakdown;
        total_cost: number;
        price_quoted: number;
        margin_absolute: number;
        margin_percent: number;
    };
}
