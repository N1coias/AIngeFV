from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.sql import func

from backend.app.database import Base


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True)
    manufacturer = Column(String(120), default="")
    family = Column(String(180), default="")
    model = Column(String(220), nullable=False)
    pmax_w = Column(Float, nullable=False)
    voc_v = Column(Float, nullable=False)
    vmp_v = Column(Float, nullable=False)
    isc_a = Column(Float, nullable=False)
    imp_a = Column(Float, nullable=False)
    beta_voc_pct_c = Column(Float, nullable=False)
    beta_vmp_pct_c = Column(Float, nullable=False)
    source_filename = Column(String(255), default="")
    datasheet_sha256 = Column(String(64), default="")
    confirmed = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "manufacturer",
            "family",
            "model",
            "pmax_w",
            name="uq_module_variant",
        ),
    )


class Inverter(Base):
    __tablename__ = "inverters"

    id = Column(Integer, primary_key=True)
    manufacturer = Column(String(120), default="")
    model = Column(String(220), nullable=False, unique=True)
    pac_w = Column(Float, nullable=False)
    max_dc_voltage_v = Column(Float, nullable=False)
    mppt_min_v = Column(Float, nullable=False)
    mppt_max_v = Column(Float, nullable=False)
    mppt_count = Column(Integer, nullable=False)
    inputs_per_mppt = Column(Integer, nullable=False)
    max_current_per_mppt_a = Column(Float, nullable=False)
    max_current_per_string_a = Column(Float, nullable=False)
    max_short_circuit_per_mppt_a = Column(Float, nullable=False)
    source_filename = Column(String(255), default="")
    datasheet_sha256 = Column(String(64), default="")
    confirmed = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    name = Column(String(220), nullable=False)
    client = Column(String(220), default="")
    location = Column(String(220), default="")
    roof_type = Column(String(120), default="")
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
