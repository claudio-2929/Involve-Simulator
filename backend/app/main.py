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
