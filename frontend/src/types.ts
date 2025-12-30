export interface Platform {
    id: number;
    name: string;
    capex: number;
    launch_cost: number;
    max_payload_mass: number;
    min_altitude: number;
    max_altitude: number;
    max_duration_days: number;
    power_available_payload: number;
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
        survives_night: boolean;
        margin_wh: number;
        status: string;
    };
    flight_analysis: {
        wind_volatility_score: number;
        station_keeping_prob: number;
        overprovisioning_factor: number;
        drift_risk: string;
    };
    quote: {
        breakdown: QuoteBreakdown;
        total_cost: number;
        price_quoted: number;
        margin_absolute: number;
        margin_percent: number;
    };
}
