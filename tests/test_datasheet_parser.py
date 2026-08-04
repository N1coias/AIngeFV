from backend.app.services.datasheets import (
    parse_inverter_document,
    parse_module_tables,
)


def test_module_table_parser_returns_all_variants():
    document = {
        "text": (
            "JA SOLAR JAM72D40 "
            "Temperature Coefficient of Voc -0.260 %/°C "
            "Temperature Coefficient of Vmp -0.290 %/°C"
        ),
        "tables": [[
            ["Rated Maximum Power Pmax", "575", "580", "585"],
            ["Open Circuit Voltage Voc", "51.80", "52.00", "52.20"],
            ["Maximum Power Voltage Vmp", "43.40", "43.60", "43.80"],
            ["Short Circuit Current Isc", "14.10", "14.15", "14.20"],
            ["Maximum Power Current Imp", "13.25", "13.30", "13.36"],
        ]],
        "method": "test",
        "sha256": "abc",
    }

    result = parse_module_tables(document, "ja.pdf")
    assert len(result["variants"]) == 3
    assert result["variants"][2]["pmax_w"] == 585
    assert result["beta_voc_pct_c"] == -0.260


def test_inverter_power_kw_is_converted_to_watts():
    document = {
        "text": (
            "HUAWEI SUN2000-100KTL-M2 "
            "Rated AC Active Power 100 kW "
            "Maximum Input Voltage 1100 V "
            "MPPT operating range 200 V - 1000 V "
            "Number of MPPTs 10 "
            "Inputs per MPPT 2 "
            "Maximum current per MPPT 30 A "
            "Maximum current per input 20 A "
            "Maximum short circuit current per MPPT 40 A"
        ),
        "tables": [],
        "method": "test",
        "sha256": "abc",
    }

    result = parse_inverter_document(document, "huawei.pdf")
    assert result["inverter"]["pac_w"] == 100000
    assert result["inverter"]["max_dc_voltage_v"] == 1100
    assert result["inverter"]["mppt_count"] == 10
