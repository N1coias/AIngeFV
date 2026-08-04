from typing import Literal

from pydantic import BaseModel, Field


class ModuleIn(BaseModel):
    manufacturer: str = ""
    family: str = ""
    model: str
    pmax_w: float = Field(gt=0)
    voc_v: float = Field(gt=0)
    vmp_v: float = Field(gt=0)
    isc_a: float = Field(gt=0)
    imp_a: float = Field(gt=0)
    beta_voc_pct_c: float
    beta_vmp_pct_c: float
    source_filename: str = ""
    datasheet_sha256: str = ""
    confirmed: bool = True


class InverterIn(BaseModel):
    manufacturer: str = ""
    model: str
    pac_w: float = Field(gt=0)
    max_dc_voltage_v: float = Field(gt=0)
    mppt_min_v: float = Field(gt=0)
    mppt_max_v: float = Field(gt=0)
    mppt_count: int = Field(gt=0)
    inputs_per_mppt: int = Field(gt=0)
    max_current_per_mppt_a: float = Field(gt=0)
    max_current_per_string_a: float = Field(gt=0)
    max_short_circuit_per_mppt_a: float = Field(gt=0)
    source_filename: str = ""
    datasheet_sha256: str = ""
    confirmed: bool = True


class CableIn(BaseModel):
    one_way_length_m: float = Field(gt=0)
    material: Literal["copper", "aluminium"] = "copper"
    selected_section_mm2: float = Field(default=6, gt=0)
    maximum_voltage_drop_pct: float = Field(default=1.5, gt=0)
    conductor_temperature_c: float = Field(default=70, ge=-20, le=120)


class CalculationRequest(BaseModel):
    module: ModuleIn
    inverter: InverterIn
    total_modules: int = Field(gt=0)
    tmin_c: float
    tmax_cell_c: float
    margin_pct: float = Field(default=2.0, ge=0, le=10)
    bifacial_gain_pct: float = Field(default=0.0, ge=0, le=100)
    one_string_per_mppt: bool = True
    cable: CableIn | None = None


class ProjectIn(BaseModel):
    name: str
    client: str = ""
    location: str = ""
    roof_type: str = ""
    payload: dict
