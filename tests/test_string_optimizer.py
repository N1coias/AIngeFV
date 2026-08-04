from aingefv_engine import (
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


def test_minimum_strings_are_strictly_prioritised():
    module, inverter = equipment()
    result = calculate_dc(
        module,
        inverter,
        CalculationInput(210, -10, 70, 2, 0, True),
    )

    assert result["minimum_theoretical_strings"] == 12
    assert result["recommended"]["strings"] == 12
    assert result["recommended"]["distribution"]["label"] == "6×18 + 6×17"


def test_no_mppt_mixes_different_string_lengths():
    module, inverter = equipment()
    result = calculate_dc(
        module,
        inverter,
        CalculationInput(210, -10, 70, 2, 0, False),
    )

    for inverter_layout in result["recommended"]["mppt_layout"]["inverters"]:
        for mppt in inverter_layout["mppts"]:
            assert isinstance(mppt["modules_per_string"], int)
            assert mppt["parallel_strings"] in {1, 2}
            # Un MPPT se representa con una única longitud.
            assert set(mppt) >= {
                "modules_per_string",
                "parallel_strings",
            }


def test_parallel_mode_groups_only_equal_strings():
    module, inverter = equipment()
    result = calculate_dc(
        module,
        inverter,
        CalculationInput(210, -10, 70, 2, 0, False),
    )

    groups = [
        mppt
        for inverter_layout in result["recommended"]["mppt_layout"]["inverters"]
        for mppt in inverter_layout["mppts"]
    ]

    assert len(groups) == 6
    assert sorted(
        (group["modules_per_string"], group["parallel_strings"])
        for group in groups
    ) == [(17, 2)] * 3 + [(18, 2)] * 3


def test_maximum_voltage_alternative_is_present():
    module, inverter = equipment()
    result = calculate_dc(
        module,
        inverter,
        CalculationInput(210, -10, 70, 2, 0, True),
    )

    labels = {
        item["distribution"]["label"]
        for item in result["alternatives"]
    }
    assert "11×18 + 1×12" in labels


def test_uniform_alternative_is_present_even_with_more_strings():
    module, inverter = equipment()
    result = calculate_dc(
        module,
        inverter,
        CalculationInput(210, -10, 70, 2, 0, True),
    )

    assert any(
        item["distribution"]["label"] == "14×15"
        for item in result["alternatives"]
    )


def test_inverters_are_balanced_in_recommended_layout():
    module, inverter = equipment()
    result = calculate_dc(
        module,
        inverter,
        CalculationInput(210, -10, 70, 2, 0, True),
    )

    layout = result["recommended"]["mppt_layout"]
    modules = [
        item["total_modules"]
        for item in layout["inverters"]
    ]
    strings = [
        item["total_strings"]
        for item in layout["inverters"]
    ]

    assert modules == [105, 105]
    assert strings == [6, 6]


def test_every_alternative_preserves_total_modules():
    module, inverter = equipment()
    result = calculate_dc(
        module,
        inverter,
        CalculationInput(210, -10, 70, 2, 0, True),
    )

    for alternative in result["alternatives"]:
        total = sum(
            item["modules_per_string"] * item["string_count"]
            for item in alternative["distribution"]["lengths"]
        )
        assert total == 210
