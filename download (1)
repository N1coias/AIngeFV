import pytest

from aingefv_engine import (
    CableInput,
    CalculationInput,
    InverterData,
    ModuleData,
    calculate_dc,
)


def equipment():
    module = ModuleData(
        model="JA Solar",
        pmax_w=595,
        voc_v=52.58,
        vmp_v=44.64,
        isc_a=13.99,
        imp_a=13.33,
        beta_voc_pct_c=-0.260,
        beta_vmp_pct_c=-0.290,
    )
    inverter = InverterData(
        model="Huawei 100KTL",
        pac_w=100000,
        max_dc_voltage_v=1100,
        mppt_min_v=200,
        mppt_max_v=1000,
        mppt_count=10,
        inputs_per_mppt=2,
        max_current_per_mppt_a=30,
        max_current_per_string_a=20,
        max_short_circuit_per_mppt_a=40,
    )
    return module, inverter


def test_reference_case_allows_18_and_rejects_19():
    module, inverter = equipment()
    result = calculate_dc(
        module,
        inverter,
        CalculationInput(
            total_modules=210,
            tmin_c=-10,
            tmax_cell_c=70,
            margin_pct=2,
            one_string_per_mppt=True,
        ),
    )

    assert result["maximum_modules_by_voc"] == 18
    assert result["maximum_modules_per_string"] == 18
    assert result["recommended"]["distribution"]["maximum_length"] == 18
    assert result["superior_configuration"]["modules_per_string"] == 19
    assert result["superior_configuration"]["is_valid"] is False
    assert "supera el límite preventivo de Voc" in (
        result["superior_configuration"]["reasons"]
    )


def test_upper_mppt_limit_is_checked_with_cold_vmp():
    module, inverter = equipment()
    restricted = InverterData(
        **{
            **inverter.__dict__,
            "mppt_max_v": 800,
        }
    )
    result = calculate_dc(
        module,
        restricted,
        CalculationInput(210, -10, 70, 2, 0, True),
    )

    assert result["maximum_modules_by_mppt"] < (
        result["maximum_modules_by_voc"]
    )
    assert result["limiting_constraint"] == (
        "límite superior del rango MPPT"
    )


def test_bifaciality_does_not_change_voltage():
    module, inverter = equipment()
    base = calculate_dc(
        module,
        inverter,
        CalculationInput(210, -10, 70, 2, 0, True),
    )
    bifacial = calculate_dc(
        module,
        inverter,
        CalculationInput(210, -10, 70, 2, 20, True),
    )

    assert base["voc_module_cold_v"] == bifacial["voc_module_cold_v"]
    assert base["maximum_modules_per_string"] == (
        bifacial["maximum_modules_per_string"]
    )
    assert bifacial["imp_corrected_a"] > base["imp_corrected_a"]


def test_parallel_mode_keeps_different_lengths_in_separate_groups():
    module, inverter = equipment()
    result = calculate_dc(
        module,
        inverter,
        CalculationInput(210, -10, 70, 2, 0, False),
    )

    recommended = result["recommended"]
    distribution = recommended["distribution"]
    expected_groups = sum(
        (item["string_count"] + 1) // 2
        for item in distribution["lengths"]
    )

    assert recommended["occupied_mppts"] == expected_groups


def test_cable_temperature_and_total_losses():
    module, inverter = equipment()
    cold_cable = calculate_dc(
        module,
        inverter,
        CalculationInput(
            210,
            -10,
            70,
            2,
            0,
            True,
            CableInput(35, "copper", 6, 1.5, 20),
        ),
    )
    hot_cable = calculate_dc(
        module,
        inverter,
        CalculationInput(
            210,
            -10,
            70,
            2,
            0,
            True,
            CableInput(35, "copper", 6, 1.5, 70),
        ),
    )

    assert hot_cable["cable"]["voltage_drop_pct"] > (
        cold_cable["cable"]["voltage_drop_pct"]
    )
    assert hot_cable["cable"]["total_loss_w"] > (
        hot_cable["cable"]["loss_per_string_w"]
    )


def test_invalid_temperature_order_is_rejected():
    module, inverter = equipment()
    with pytest.raises(ValueError):
        calculate_dc(
            module,
            inverter,
            CalculationInput(210, 80, 70, 2, 0, True),
        )
