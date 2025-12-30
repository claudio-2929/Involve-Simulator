from typing import List
from fastapi import FastAPI, Depends, HTTPException, Query
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, create_engine, Session, select
from app.models import Platform, PlatformBase, Payload, PayloadBase, Client, ClientBase, MissionPreset, MissionPresetBase

# Database setup
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

def seed_data(session: Session):
    # Check if data exists
    if session.exec(select(Platform)).first():
        return

    # --- Real-World Platform Presets ---
    p1 = Platform(
        name="Involve SmartBalloon (Standard)",
        platform_type="Super-Pressure Variable Volume",
        capex=30000.0,  # €30,000
        launch_cost=2000.0,
        consumables_cost=1833.0,  # Helium, etc.
        max_payload_mass=15.0,
        min_altitude=18.0,
        max_altitude=23.0,
        max_duration_days=60,
        amortization_flights=5,
        day_power=100.0,
        night_power=40.0,
        battery_capacity=1500.0  # Wh
    )
    p2 = Platform(
        name="Heavy-Lift Stratollite",
        platform_type="Zero-Pressure with Ballast Control",
        capex=120000.0,  # €120,000
        launch_cost=8000.0,
        consumables_cost=5000.0,
        max_payload_mass=50.0,
        min_altitude=18.0,
        max_altitude=25.0,
        max_duration_days=30,
        amortization_flights=3,
        day_power=250.0,
        night_power=250.0,  # Continuous power
        battery_capacity=8000.0  # Wh
    )

    # --- Real-World Payload Presets ---
    pay1 = Payload(
        name="SAR Entry-Level (Involve Custom)",
        capex=10000.0,
        mass=4.5,
        power_consumption=45.0,
        resolution_gsd=2.0,  # 1-3m
        fov=20.0,
        daily_data_rate_gb=30.0,
        market="Maritime / Infrastructure"
    )
    pay2 = Payload(
        name="Optical High-End (PhaseOne iXM-100)",
        capex=45000.0,
        mass=1.1,
        power_consumption=16.0,
        resolution_gsd=0.05,  # <5cm GSD
        fov=45.0,
        daily_data_rate_gb=80.0,
        market="Urban Mapping / Precision Ag"
    )
    pay3 = Payload(
        name="Hyperspectral (Headwall Nano HP)",
        capex=35000.0,
        mass=1.5,
        power_consumption=20.0,
        resolution_gsd=1.0,
        fov=30.0,
        daily_data_rate_gb=100.0,
        market="Vegetation / Pollution Analysis"
    )

    session.add(p1)
    session.add(p2)
    session.add(pay1)
    session.add(pay2)
    session.add(pay3)
    session.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    with Session(engine) as session:
        seed_data(session)
    yield

app = FastAPI(lifespan=lifespan, title="Involve Stratospheric Simulator API")

@app.get("/")
def read_root():
    return {"message": "Involve Stratospheric Simulator API Online"}

# --- Platforms ---

@app.post("/platforms/", response_model=Platform)
def create_platform(platform: PlatformBase, session: Session = Depends(get_session)):
    db_platform = Platform.model_validate(platform)
    session.add(db_platform)
    session.commit()
    session.refresh(db_platform)
    return db_platform

@app.get("/platforms/", response_model=List[Platform])
def read_platforms(offset: int = 0, limit: int = Query(default=100, le=100), session: Session = Depends(get_session)):
    platforms = session.exec(select(Platform).offset(offset).limit(limit)).all()
    return platforms

@app.get("/platforms/{platform_id}", response_model=Platform)
def read_platform(platform_id: int, session: Session = Depends(get_session)):
    platform = session.get(Platform, platform_id)
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")
    return platform

@app.delete("/platforms/{platform_id}")
def delete_platform(platform_id: int, session: Session = Depends(get_session)):
    platform = session.get(Platform, platform_id)
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")
    session.delete(platform)
    session.commit()
    return {"ok": True}

@app.put("/platforms/{platform_id}", response_model=Platform)
def update_platform(platform_id: int, platform_data: PlatformBase, session: Session = Depends(get_session)):
    platform = session.get(Platform, platform_id)
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")
    platform_dict = platform_data.model_dump(exclude_unset=True)
    for key, value in platform_dict.items():
        setattr(platform, key, value)
    session.add(platform)
    session.commit()
    session.refresh(platform)
    return platform

# --- Payloads ---

@app.post("/payloads/", response_model=Payload)
def create_payload(payload: PayloadBase, session: Session = Depends(get_session)):
    db_payload = Payload.model_validate(payload)
    session.add(db_payload)
    session.commit()
    session.refresh(db_payload)
    return db_payload

@app.get("/payloads/", response_model=List[Payload])
def read_payloads(offset: int = 0, limit: int = Query(default=100, le=100), session: Session = Depends(get_session)):
    payloads = session.exec(select(Payload).offset(offset).limit(limit)).all()
    return payloads

@app.get("/payloads/{payload_id}", response_model=Payload)
def read_payload(payload_id: int, session: Session = Depends(get_session)):
    payload = session.get(Payload, payload_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Payload not found")
    return payload

@app.delete("/payloads/{payload_id}")
def delete_payload(payload_id: int, session: Session = Depends(get_session)):
    payload = session.get(Payload, payload_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Payload not found")
    session.delete(payload)
    session.commit()
    return {"ok": True}

@app.put("/payloads/{payload_id}", response_model=Payload)
def update_payload(payload_id: int, payload_data: PayloadBase, session: Session = Depends(get_session)):
    payload = session.get(Payload, payload_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Payload not found")
    payload_dict = payload_data.model_dump(exclude_unset=True)
    for key, value in payload_dict.items():
        setattr(payload, key, value)
    session.add(payload)
    session.commit()
    session.refresh(payload)
    return payload

# --- Clients ---

@app.post("/clients/", response_model=Client)
def create_client(client: ClientBase, session: Session = Depends(get_session)):
    db_client = Client.model_validate(client)
    session.add(db_client)
    session.commit()
    session.refresh(db_client)
    return db_client

@app.get("/clients/", response_model=List[Client])
def read_clients(offset: int = 0, limit: int = Query(default=100, le=100), session: Session = Depends(get_session)):
    clients = session.exec(select(Client).offset(offset).limit(limit)).all()
    return clients

# --- Mission Presets ---

@app.post("/missions/", response_model=MissionPreset)
def create_mission(mission: MissionPresetBase, session: Session = Depends(get_session)):
    db_mission = MissionPreset.model_validate(mission)
    session.add(db_mission)
    session.commit()
    session.refresh(db_mission)
    return db_mission

@app.get("/missions/", response_model=List[MissionPreset])
def read_missions(offset: int = 0, limit: int = Query(default=100, le=100), session: Session = Depends(get_session)):
    missions = session.exec(select(MissionPreset).offset(offset).limit(limit)).all()
    return missions

# --- Simulation & Quoting Logic ---

from pydantic import BaseModel
from app.engine.power import PowerModel
from app.engine.flight import FlightModel
from app.economics.pricing import PricingEngine

class SimulationRequest(BaseModel):
    platform_id: int
    payload_id: int
    lat: float
    lon: float
    month: int # 1-12
    duration_days: int
    target_radius_km: float
    margin_percent: float = 0.30

class SimulationResponse(BaseModel):
    is_feasible: bool
    warnings: List[str]
    power_analysis: dict
    flight_analysis: dict
    quote: dict

@app.post("/simulate/", response_model=SimulationResponse)
def run_simulation(req: SimulationRequest, session: Session = Depends(get_session)):
    # 1. Fetch Assets
    platform = session.get(Platform, req.platform_id)
    payload = session.get(Payload, req.payload_id)
    
    if not platform or not payload:
        raise HTTPException(status_code=404, detail="Platform or Payload not found")
        
    warnings = []
    is_feasible = True
    
    # 2. Power Simulation (using new night_power field)
    power_result = PowerModel.check_feasibility(
        lat=req.lat,
        month=req.month,
        platform_night_power=platform.night_power,
        battery_capacity_wh=platform.battery_capacity,
        payload_power_w=payload.power_consumption
    )
    
    if not power_result["is_feasible"]:
        warnings.append(f"Critical Power Shortage: Duty Cycle {power_result['duty_cycle_percent']}%")
        is_feasible = False
    elif power_result["duty_cycle_percent"] < 100:
        warnings.append(f"Reduced Duty Cycle: {power_result['duty_cycle_percent']}% operational at night")
        
    # Check Payload Weight vs Platform Capacity
    if payload.mass > platform.max_payload_mass:
        warnings.append(f"Payload Overweight: {payload.mass}kg > {platform.max_payload_mass}kg")
        is_feasible = False

    # 3. Flight Simulation (using platform_type for ACS selection)
    flight_result = FlightModel.simulate_station_keeping(
        lat=req.lat,
        month=req.month,
        target_radius_km=req.target_radius_km,
        platform_type=platform.platform_type
    )
    
    if flight_result["drift_warning"]:
        warnings.append(f"Drift Warning: Wind ({flight_result['mean_wind_speed_kmh']} km/h) exceeds ACS capability ({flight_result['acs_correction_speed_kmh']} km/h)")
    elif flight_result["drift_risk"] == "High":
        warnings.append("High Drift Risk: Fleet overprovisioning recommended")
    
    # 4. Economic Simulation
    quote_result = PricingEngine.calculate_quote(
        platform=platform.model_dump(),
        payload=payload.model_dump(),
        mission_input={"duration": req.duration_days},
        flight_result=flight_result,
        margin_percent=req.margin_percent
    )

    return {
        "is_feasible": is_feasible,
        "warnings": warnings,
        "power_analysis": power_result,
        "flight_analysis": flight_result,
        "quote": quote_result
    }


# --- Advanced Simulation (Loon-Based Physics) ---

from app.engine.wind import WindField
from app.engine.navigator import Navigator
from app.engine.fleet import FleetOrchestrator
from app.engine.payload_physics import SensorGeometry
from app.engine.monte_carlo import MonteCarloSimulator
from dataclasses import asdict


class AdvancedSimulationRequest(BaseModel):
    platform_id: int
    payload_id: int
    lat: float
    lon: float
    month: int
    duration_days: int
    target_radius_km: float
    margin_percent: float = 0.30
    run_monte_carlo: bool = True
    monte_carlo_iterations: int = 30


class AdvancedSimulationResponse(BaseModel):
    is_feasible: bool
    warnings: List[str]
    power_analysis: dict
    flight_analysis: dict
    # New advanced sections
    wind_profile: dict
    station_keeping: dict
    fleet_analysis: dict
    payload_performance: dict
    monte_carlo_risk: dict
    quote: dict


@app.post("/simulate/advanced/", response_model=AdvancedSimulationResponse)
def run_advanced_simulation(req: AdvancedSimulationRequest, session: Session = Depends(get_session)):
    """
    Advanced simulation using Loon-inspired physics:
    - 4D Wind-Based Navigation
    - Station Keeping with ACS logic
    - Fleet Orchestration and Overprovisioning
    - Altitude-Dependent Sensor Performance
    - Monte Carlo Risk Assessment
    """
    # 1. Fetch Assets
    platform = session.get(Platform, req.platform_id)
    payload = session.get(Payload, req.payload_id)
    
    if not platform or not payload:
        raise HTTPException(status_code=404, detail="Platform or Payload not found")
        
    warnings = []
    is_feasible = True
    
    # 2. Wind Profile at Target Location
    wind_profile = {}
    for alt, wind in WindField.get_wind_profile(req.lat, req.lon, req.month).items():
        wind_profile[f"{alt}km"] = {
            "speed_kmh": wind.speed_kmh,
            "direction_deg": wind.direction_deg
        }
    
    # Find optimal altitude for station keeping
    optimal_alt, heading_error = WindField.get_optimal_altitude(
        req.lat, req.lon, target_heading_deg=0, month=req.month,
        altitude_range=(platform.min_altitude, platform.max_altitude)
    )
    
    # 3. Station Keeping Simulation (48h sample for speed)
    sim_hours = min(req.duration_days * 24, 48)
    sk_result = Navigator.simulate_station_keeping(
        start_lat=req.lat,
        start_lon=req.lon,
        target_lat=req.lat,
        target_lon=req.lon,
        aoi_radius_km=req.target_radius_km,
        mission_hours=sim_hours,
        month=req.month,
        platform_min_alt=platform.min_altitude,
        platform_max_alt=platform.max_altitude,
        initial_altitude_km=optimal_alt
    )
    
    station_keeping = {
        "simulation_hours": sk_result.total_hours,
        "time_on_target_hours": sk_result.time_on_target_hours,
        "time_repositioning_hours": sk_result.time_repositioning_hours,
        "drift_events": sk_result.drift_events,
        "altitude_changes": sk_result.altitude_changes,
        "energy_used_wh": sk_result.total_energy_used_wh,
        "coverage_percent": sk_result.coverage_percent,
        "optimal_altitude_km": optimal_alt
    }
    
    if sk_result.coverage_percent < 70:
        warnings.append(f"Low Coverage: Only {sk_result.coverage_percent}% time on target")
        if sk_result.coverage_percent < 50:
            is_feasible = False
    
    # 4. Power Analysis
    power_result = PowerModel.check_feasibility(
        lat=req.lat,
        month=req.month,
        platform_night_power=platform.night_power,
        battery_capacity_wh=platform.battery_capacity,
        payload_power_w=payload.power_consumption
    )
    
    # Add ACS energy overhead
    daily_acs_energy = (sk_result.total_energy_used_wh / sim_hours) * 24

    power_result["daily_acs_energy_wh"] = round(daily_acs_energy, 1)
    
    if not power_result["is_feasible"]:
        warnings.append(f"Critical Power Shortage: Duty Cycle {power_result['duty_cycle_percent']}%")
        is_feasible = False
        
    if payload.mass > platform.max_payload_mass:
        warnings.append(f"Payload Overweight: {payload.mass}kg > {platform.max_payload_mass}kg")
        is_feasible = False

    # 5. Fleet Analysis
    fleet_result = FleetOrchestrator.recommend_fleet_size(
        target_lat=req.lat,
        target_lon=req.lon,
        aoi_radius_km=req.target_radius_km,
        mission_days=min(req.duration_days, 7),  # Sample period
        month=req.month,
        target_availability=0.90
    )
    
    fleet_analysis = {
        "recommended_fleet_size": fleet_result["recommended_fleet_size"],
        "expected_availability_percent": fleet_result["expected_availability_percent"],
        "overprovisioning_factor": fleet_result["overprovisioning_factor"],
        "meets_90_percent_availability": fleet_result["meets_target"]
    }
    
    # 6. Payload Performance at Variable Altitude
    avg_altitude = (platform.min_altitude + platform.max_altitude) / 2
    perf = SensorGeometry.calculate_imaging_performance(
        base_gsd_m=payload.resolution_gsd,
        fov_deg=payload.fov,
        altitude_km=avg_altitude,
        ground_speed_kmh=20,  # Typical stratospheric drift
        off_nadir_deg=0
    )
    
    coverage_analysis = SensorGeometry.analyze_mission_coverage(
        base_gsd_m=payload.resolution_gsd,
        fov_deg=payload.fov,
        min_altitude_km=platform.min_altitude,
        max_altitude_km=platform.max_altitude,
        average_ground_speed_kmh=20,
        station_keeping_coverage_percent=sk_result.coverage_percent
    )
    
    payload_performance = {
        "effective_gsd_m": coverage_analysis.effective_gsd_m,
        "gsd_range_m": f"{coverage_analysis.min_gsd_m} - {coverage_analysis.max_gsd_m}",
        "average_swath_km": coverage_analysis.average_swath_km,
        "repositioning_loss_percent": coverage_analysis.repositioning_coverage_loss_percent,
        "effective_coverage_percent": coverage_analysis.effective_coverage_percent,
        "coverage_rate_km2_h": perf.coverage_rate_km2_h
    }
    
    # 7. Monte Carlo Risk Assessment
    monte_carlo_risk = {}
    if req.run_monte_carlo:
        mc_result = MonteCarloSimulator.run_simulation(
            lat=req.lat,
            lon=req.lon,
            aoi_radius_km=req.target_radius_km,
            mission_days=req.duration_days,
            month=req.month,
            platform_min_alt=platform.min_altitude,
            platform_max_alt=platform.max_altitude,
            payload_gsd_m=payload.resolution_gsd,
            payload_fov_deg=payload.fov,
            n_iterations=req.monte_carlo_iterations
        )
        
        monte_carlo_risk = {
            "service_reliability_percent": mc_result.service_reliability_percent,
            "reliability_95_confidence": f"{mc_result.service_reliability_p5}% - {mc_result.service_reliability_p95}%",
            "expected_drift_events": mc_result.expected_drift_events,
            "launch_abort_probability_percent": mc_result.launch_abort_probability,
            "recommended_overprovisioning": mc_result.recommended_overprovisioning,
            "risk_level": mc_result.risk_level,
            "mission_feasibility": mc_result.mission_feasibility
        }
        
        if mc_result.risk_level in ["High", "Critical"]:
            warnings.append(f"Monte Carlo Risk: {mc_result.risk_level} - {mc_result.mission_feasibility}")
    
    # 8. Original flight analysis for compatibility
    flight_result = FlightModel.simulate_station_keeping(
        lat=req.lat,
        month=req.month,
        target_radius_km=req.target_radius_km,
        platform_type=platform.platform_type
    )
    
    # Update overprovisioning with Monte Carlo recommendation
    if monte_carlo_risk.get("recommended_overprovisioning"):
        flight_result["overprovisioning_factor"] = max(
            flight_result["overprovisioning_factor"],
            monte_carlo_risk["recommended_overprovisioning"]
        )
    
    # 9. Quote with advanced overprovisioning
    quote_result = PricingEngine.calculate_quote(
        platform=platform.model_dump(),
        payload=payload.model_dump(),
        mission_input={"duration": req.duration_days},
        flight_result=flight_result,
        margin_percent=req.margin_percent
    )

    return {
        "is_feasible": is_feasible,
        "warnings": warnings,
        "power_analysis": power_result,
        "flight_analysis": flight_result,
        "wind_profile": wind_profile,
        "station_keeping": station_keeping,
        "fleet_analysis": fleet_analysis,
        "payload_performance": payload_performance,
        "monte_carlo_risk": monte_carlo_risk,
        "quote": quote_result
    }


# --- Analysis Endpoints for Sensitivity Analysis ---

class SeasonalityRequest(BaseModel):
    platform_id: int
    payload_id: int
    lat: float
    lon: float
    duration_days: int
    target_radius_km: float
    margin_percent: float = 0.30


class SeasonalityDataPoint(BaseModel):
    month: int
    month_name: str
    cost: float
    is_feasible: bool
    overprovisioning_factor: float
    service_reliability: float
    risk_level: str


class SeasonalityResponse(BaseModel):
    data: List[SeasonalityDataPoint]
    best_month: int
    worst_month: int
    cost_variance_percent: float
    recommendation: str


@app.post("/analyze/seasonality", response_model=SeasonalityResponse)
def analyze_seasonality(req: SeasonalityRequest, session: Session = Depends(get_session)):
    """
    Analyze mission cost and feasibility across all 12 months.
    Answers: "How much do I save launching in June vs January?"
    """
    platform = session.get(Platform, req.platform_id)
    payload = session.get(Payload, req.payload_id)
    
    if not platform or not payload:
        raise HTTPException(status_code=404, detail="Platform or Payload not found")
    
    month_names = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", 
                   "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
    
    results = []
    
    for month in range(1, 13):
        # Quick simulation for each month
        flight_result = FlightModel.simulate_station_keeping(
            lat=req.lat,
            month=month,
            target_radius_km=req.target_radius_km,
            platform_type=platform.platform_type
        )
        
        power_result = PowerModel.check_feasibility(
            lat=req.lat,
            month=month,
            platform_night_power=platform.night_power,
            battery_capacity_wh=platform.battery_capacity,
            payload_power_w=payload.power_consumption
        )
        
        quote = PricingEngine.calculate_quote(
            platform=platform.model_dump(),
            payload=payload.model_dump(),
            mission_input={"duration": req.duration_days},
            flight_result=flight_result,
            margin_percent=req.margin_percent
        )
        
        # Determine risk level from overprovisioning
        overprov = flight_result["overprovisioning_factor"]
        if overprov <= 1.2:
            risk = "Low"
        elif overprov <= 1.8:
            risk = "Medium"
        else:
            risk = "High"
        
        is_feasible = power_result["is_feasible"] and not flight_result["drift_warning"]
        
        # Estimate service reliability from coverage probability
        reliability = min(95, flight_result["station_keeping_prob"] * 100)
        
        results.append(SeasonalityDataPoint(
            month=month,
            month_name=month_names[month - 1],
            cost=quote["price_quoted"],
            is_feasible=is_feasible,
            overprovisioning_factor=overprov,
            service_reliability=round(reliability, 1),
            risk_level=risk
        ))
    
    # Find best/worst months
    feasible_results = [r for r in results if r.is_feasible]
    if feasible_results:
        best = min(feasible_results, key=lambda x: x.cost)
        worst = max(feasible_results, key=lambda x: x.cost)
    else:
        best = min(results, key=lambda x: x.cost)
        worst = max(results, key=lambda x: x.cost)
    
    # Calculate variance
    costs = [r.cost for r in results]
    variance = ((max(costs) - min(costs)) / min(costs)) * 100 if min(costs) > 0 else 0
    
    # Generate recommendation
    low_cost_months = [r.month_name for r in results if r.cost <= best.cost * 1.1]
    high_cost_months = [r.month_name for r in results if r.cost >= worst.cost * 0.9]
    
    recommendation = f"Lancia tra {', '.join(low_cost_months[:3])} per risparmiare fino al {variance:.0f}%. Evita {', '.join(high_cost_months[:2])}."
    
    return SeasonalityResponse(
        data=results,
        best_month=best.month,
        worst_month=worst.month,
        cost_variance_percent=round(variance, 1),
        recommendation=recommendation
    )


class GeographicRequest(BaseModel):
    platform_id: int
    payload_id: int
    month: int
    duration_days: int
    target_radius_km: float
    # Bounding box for analysis
    lat_min: float = 30.0
    lat_max: float = 60.0
    lon_min: float = -10.0
    lon_max: float = 30.0
    grid_resolution: int = 5  # Points per axis


class GeographicDataPoint(BaseModel):
    lat: float
    lon: float
    feasibility_score: float  # 0-100
    cost_factor: float  # Multiplier vs best case
    limiting_factor: str  # "power", "drift", "none"


class GeographicResponse(BaseModel):
    data: List[GeographicDataPoint]
    optimal_lat: float
    optimal_lon: float
    coverage_summary: str


@app.post("/analyze/geographic", response_model=GeographicResponse)
def analyze_geographic(req: GeographicRequest, session: Session = Depends(get_session)):
    """
    Generate feasibility heatmap across geographic region.
    Answers: "Is it easier to monitor Sicily or Scotland?"
    """
    platform = session.get(Platform, req.platform_id)
    payload = session.get(Payload, req.payload_id)
    
    if not platform or not payload:
        raise HTTPException(status_code=404, detail="Platform or Payload not found")
    
    results = []
    best_score = 0
    optimal_location = (0, 0)
    
    lat_step = (req.lat_max - req.lat_min) / req.grid_resolution
    lon_step = (req.lon_max - req.lon_min) / req.grid_resolution
    
    base_cost = None  # For cost factor calculation
    
    for i in range(req.grid_resolution + 1):
        for j in range(req.grid_resolution + 1):
            lat = req.lat_min + i * lat_step
            lon = req.lon_min + j * lon_step
            
            # Quick feasibility check
            flight_result = FlightModel.simulate_station_keeping(
                lat=lat,
                month=req.month,
                target_radius_km=req.target_radius_km,
                platform_type=platform.platform_type
            )
            
            power_result = PowerModel.check_feasibility(
                lat=lat,
                month=req.month,
                platform_night_power=platform.night_power,
                battery_capacity_wh=platform.battery_capacity,
                payload_power_w=payload.power_consumption
            )
            
            quote = PricingEngine.calculate_quote(
                platform=platform.model_dump(),
                payload=payload.model_dump(),
                mission_input={"duration": req.duration_days},
                flight_result=flight_result,
                margin_percent=0.25
            )
            
            if base_cost is None:
                base_cost = quote["price_quoted"]
            
            # Calculate feasibility score (0-100)
            power_score = power_result["duty_cycle_percent"]
            drift_score = flight_result["station_keeping_prob"] * 100
            feasibility = (power_score + drift_score) / 2
            
            # Determine limiting factor
            if power_score < drift_score:
                limiting = "power"
            elif drift_score < power_score * 0.8:
                limiting = "drift"
            else:
                limiting = "none"
            
            # Cost factor
            cost_factor = quote["price_quoted"] / base_cost if base_cost > 0 else 1
            
            results.append(GeographicDataPoint(
                lat=round(lat, 2),
                lon=round(lon, 2),
                feasibility_score=round(feasibility, 1),
                cost_factor=round(cost_factor, 2),
                limiting_factor=limiting
            ))
            
            if feasibility > best_score:
                best_score = feasibility
                optimal_location = (lat, lon)
    
    # Summary
    power_limited = len([r for r in results if r.limiting_factor == "power"])
    drift_limited = len([r for r in results if r.limiting_factor == "drift"])
    total = len(results)
    
    summary = f"{power_limited}/{total} punti power-limited, {drift_limited}/{total} drift-limited. Location ottimale: {optimal_location[0]:.1f}°N, {optimal_location[1]:.1f}°E"
    
    return GeographicResponse(
        data=results,
        optimal_lat=optimal_location[0],
        optimal_lon=optimal_location[1],
        coverage_summary=summary
    )
