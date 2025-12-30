from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship

# --- Shared Models ---

class PlatformBase(SQLModel):
    name: str = Field(index=True)
    platform_type: str = Field(default="Super-Pressure")  # e.g., "Super-Pressure Variable Volume", "Zero-Pressure"
    capex: float
    launch_cost: float
    consumables_cost: float = Field(default=0.0)  # e.g., helium, ballast
    max_payload_mass: float # kg
    min_altitude: float # km
    max_altitude: float # km
    max_duration_days: int
    amortization_flights: int # e.g., 5 flights
    day_power: float  # Watts available during day
    night_power: float  # Watts available during night (battery limited)
    battery_capacity: float # Watt-hours (Wh)

class Platform(PlatformBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    missions: List["MissionPreset"] = Relationship(back_populates="platform")

class PayloadBase(SQLModel):
    name: str = Field(index=True)
    capex: float
    mass: float # kg
    power_consumption: float # Watts
    resolution_gsd: float # m
    fov: float # degrees
    daily_data_rate_gb: float # GB/day
    market: str = Field(default="General")  # e.g., "Maritime", "Agriculture", "Urban"

class Payload(PayloadBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    missions: List["MissionPreset"] = Relationship(back_populates="payload")

class ClientBase(SQLModel):
    name: str = Field(index=True)
    discount_rate: float = Field(default=0.0)

class Client(ClientBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    quotes: List["Quote"] = Relationship(back_populates="client")

class MissionPresetBase(SQLModel):
    name: str
    target_lat: float
    target_lon: float
    duration_days: int
    platform_id: Optional[int] = Field(default=None, foreign_key="platform.id")
    payload_id: Optional[int] = Field(default=None, foreign_key="payload.id")

class MissionPreset(MissionPresetBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    platform: Optional[Platform] = Relationship(back_populates="missions")
    payload: Optional[Payload] = Relationship(back_populates="missions")

# --- Quote/Result Models (Not always stored, but good for history) ---

class QuoteBase(SQLModel):
    mission_name: str
    total_price: float
    margin: float
    client_id: Optional[int] = Field(default=None, foreign_key="client.id")

class Quote(QuoteBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    client: Optional[Client] = Relationship(back_populates="quotes")
