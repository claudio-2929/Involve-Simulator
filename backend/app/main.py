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

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    # Seed data if empty could go here
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

# --- Data Seeding ---

def seed_data(session: Session):
    # Check if data exists
    if session.exec(select(Platform)).first():
        return

    # Platforms
    p1 = Platform(
        name="SmartBalloon Mk1",
        capex=15000.0,
        launch_cost=5000.0,
        max_payload_mass=15.0,
        min_altitude=18.0,
        max_altitude=25.0,
        max_duration_days=100,
        amortization_flights=3,
        power_available_payload=150.0,
        battery_capacity=2000.0 # Wh
    )
    p2 = Platform(
        name="PseudoSat Alpha",
        capex=45000.0,
        launch_cost=12000.0,
        max_payload_mass=25.0,
        min_altitude=20.0,
        max_altitude=30.0,
        max_duration_days=180,
        amortization_flights=5,
        power_available_payload=300.0,
        battery_capacity=5000.0 # Wh
    )

    # Payloads
    pay1 = Payload(
        name="Optical High-Res (EOS-1)",
        capex=25000.0,
        mass=5.0,
        power_consumption=45.0,
        resolution_gsd=0.3,
        fov=15.0,
        daily_data_rate_gb=50.0
    )
    pay2 = Payload(
        name="SAR Radar (S-Band)",
        capex=85000.0,
        mass=12.0,
        power_consumption=120.0,
        resolution_gsd=1.0,
        fov=25.0,
        daily_data_rate_gb=120.0
    )

    session.add(p1)
    session.add(p2)
    session.add(pay1)
    session.add(pay2)
    session.commit()

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
    
    # 2. Power Simulation
    power_result = PowerModel.check_feasibility(
        lat=req.lat,
        month=req.month,
        platform_power_bonus=platform.power_available_payload,
        battery_capacity_wh=platform.battery_capacity,
        payload_power_w=payload.power_consumption
    )
    
    if not power_result["survives_night"]:
        warnings.append("Insufficient Battery for Night Operations")
        
    # Check Payload Weight vs Platform Capacity
    if payload.mass > platform.max_payload_mass:
        warnings.append(f"Payload Overweight: {payload.mass}kg > {platform.max_payload_mass}kg")

    # 3. Flight Simulation
    flight_result = FlightModel.simulate_station_keeping(
        lat=req.lat,
        month=req.month,
        target_radius_km=req.target_radius_km
    )
    
    if flight_result["drift_risk"] == "High":
        warnings.append("High Drift Risk: Requires large fleet overprovisioning")

    # 4. Economic Simulation
    # Convert SQLModel objects to dicts for the engine
    quote_result = PricingEngine.calculate_quote(
        platform=platform.model_dump(),
        payload=payload.model_dump(),
        mission_input={"duration": req.duration_days},
        flight_result=flight_result,
        margin_percent=req.margin_percent
    )

    return {
        "is_feasible": len(warnings) == 0 or (len(warnings) == 1 and "Drift" in warnings[0]), # Allow drift warn, fail on power/mass
        "warnings": warnings,
        "power_analysis": power_result,
        "flight_analysis": flight_result,
        "quote": quote_result
    }

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    with Session(engine) as session:
        seed_data(session)
    yield
