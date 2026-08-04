from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def payload():
    return {
        "module": {
            "manufacturer": "JA Solar",
            "family": "JAM72D40",
            "model": "JAM72D40",
            "pmax_w": 595,
            "voc_v": 52.58,
            "vmp_v": 44.64,
            "isc_a": 13.99,
            "imp_a": 13.33,
            "beta_voc_pct_c": -0.260,
            "beta_vmp_pct_c": -0.290,
            "source_filename": "",
            "datasheet_sha256": "",
            "confirmed": True,
        },
        "inverter": {
            "manufacturer": "Huawei",
            "model": "SUN2000-100KTL-M2",
            "pac_w": 100000,
            "max_dc_voltage_v": 1100,
            "mppt_min_v": 200,
            "mppt_max_v": 1000,
            "mppt_count": 10,
            "inputs_per_mppt": 2,
            "max_current_per_mppt_a": 30,
            "max_current_per_string_a": 20,
            "max_short_circuit_per_mppt_a": 40,
            "source_filename": "",
            "datasheet_sha256": "",
            "confirmed": True,
        },
        "total_modules": 210,
        "tmin_c": -10,
        "tmax_cell_c": 70,
        "margin_pct": 2,
        "bifacial_gain_pct": 0,
        "one_string_per_mppt": True,
        "cable": {
            "one_way_length_m": 35,
            "material": "copper",
            "selected_section_mm2": 6,
            "maximum_voltage_drop_pct": 1.5,
            "conductor_temperature_c": 70,
        },
    }


def test_health_and_readiness():
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/health/ready").status_code == 200


def test_calculation_endpoint():
    response = client.post("/api/calculate/dc", json=payload())
    assert response.status_code == 200
    data = response.json()
    assert data["maximum_modules_per_string"] == 18
    assert data["superior_configuration"]["is_valid"] is False


def test_invalid_extension_is_rejected():
    response = client.post(
        "/api/datasheet/module",
        files={
            "file": (
                "datasheet.txt",
                b"not a pdf",
                "text/plain",
            )
        },
    )
    assert response.status_code == 400
