from fastapi import APIRouter, HTTPException

from aingefv_engine import (
    CableInput,
    CalculationInput,
    InverterData,
    ModuleData,
    calculate_dc,
)
from backend.app.schemas import CalculationRequest

router = APIRouter()


@router.post("/dc")
def calculate(payload: CalculationRequest) -> dict:
    cable = (
        CableInput(**payload.cable.model_dump())
        if payload.cable
        else None
    )

    try:
        return calculate_dc(
            ModuleData(
                model=payload.module.model,
                pmax_w=payload.module.pmax_w,
                voc_v=payload.module.voc_v,
                vmp_v=payload.module.vmp_v,
                isc_a=payload.module.isc_a,
                imp_a=payload.module.imp_a,
                beta_voc_pct_c=payload.module.beta_voc_pct_c,
                beta_vmp_pct_c=payload.module.beta_vmp_pct_c,
            ),
            InverterData(
                model=payload.inverter.model,
                pac_w=payload.inverter.pac_w,
                max_dc_voltage_v=payload.inverter.max_dc_voltage_v,
                mppt_min_v=payload.inverter.mppt_min_v,
                mppt_max_v=payload.inverter.mppt_max_v,
                mppt_count=payload.inverter.mppt_count,
                inputs_per_mppt=payload.inverter.inputs_per_mppt,
                max_current_per_mppt_a=(
                    payload.inverter.max_current_per_mppt_a
                ),
                max_current_per_string_a=(
                    payload.inverter.max_current_per_string_a
                ),
                max_short_circuit_per_mppt_a=(
                    payload.inverter.max_short_circuit_per_mppt_a
                ),
            ),
            CalculationInput(
                total_modules=payload.total_modules,
                tmin_c=payload.tmin_c,
                tmax_cell_c=payload.tmax_cell_c,
                margin_pct=payload.margin_pct,
                bifacial_gain_pct=payload.bifacial_gain_pct,
                one_string_per_mppt=payload.one_string_per_mppt,
                cable=cable,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
