from __future__ import annotations

from collections import Counter
from functools import lru_cache
from dataclasses import asdict, dataclass
from math import ceil, floor, isfinite
from typing import Literal


@dataclass(frozen=True)
class ModuleData:
    model: str
    pmax_w: float
    voc_v: float
    vmp_v: float
    isc_a: float
    imp_a: float
    beta_voc_pct_c: float
    beta_vmp_pct_c: float


@dataclass(frozen=True)
class InverterData:
    model: str
    pac_w: float
    max_dc_voltage_v: float
    mppt_min_v: float
    mppt_max_v: float
    mppt_count: int
    inputs_per_mppt: int
    max_current_per_mppt_a: float
    max_current_per_string_a: float
    max_short_circuit_per_mppt_a: float


@dataclass(frozen=True)
class CableInput:
    one_way_length_m: float
    material: Literal["copper", "aluminium"] = "copper"
    selected_section_mm2: float = 6.0
    maximum_voltage_drop_pct: float = 1.5
    conductor_temperature_c: float = 70.0


@dataclass(frozen=True)
class CalculationInput:
    total_modules: int
    tmin_c: float
    tmax_cell_c: float
    margin_pct: float = 2.0
    bifacial_gain_pct: float = 0.0
    one_string_per_mppt: bool = True
    cable: CableInput | None = None


def voltage_at_temperature(
    value_stc: float,
    coefficient_pct_c: float,
    temperature_c: float,
) -> float:
    return value_stc * (
        1 + (coefficient_pct_c / 100.0) * (temperature_c - 25.0)
    )


def _validate_positive(name: str, value: float) -> None:
    if not isfinite(value) or value <= 0:
        raise ValueError(f"{name} debe ser un valor positivo.")


def _distribution_from_lengths(lengths: list[int]) -> dict:
    counts = Counter(lengths)
    ordered = sorted(counts.items(), reverse=True)
    label = " + ".join(
        f"{count}×{length}" for length, count in ordered
    )
    minimum = min(lengths)
    maximum = max(lengths)
    return {
        "lengths": [
            {
                "modules_per_string": length,
                "string_count": count,
            }
            for length, count in ordered
        ],
        "minimum_length": minimum,
        "maximum_length": maximum,
        "spread": maximum - minimum,
        "distinct_lengths": len(ordered),
        "maximum_length_count": counts[maximum],
        "minimum_length_count": counts[minimum],
        "average_modules_per_string": sum(lengths) / len(lengths),
        "label": label,
    }


def _balanced_lengths(
    total_modules: int,
    string_count: int,
    minimum_length: int,
    maximum_length: int,
) -> list[int] | None:
    low = total_modules // string_count
    high = ceil(total_modules / string_count)
    if low < minimum_length or high > maximum_length:
        return None
    high_count = total_modules - low * string_count
    return (
        [high] * high_count
        + [low] * (string_count - high_count)
    )


def _maximum_voltage_lengths(
    total_modules: int,
    string_count: int,
    minimum_length: int,
    maximum_length: int,
) -> list[int] | None:
    deficit = string_count * maximum_length - total_modules
    if deficit < 0:
        return None
    if deficit == 0:
        return [maximum_length] * string_count

    capacity_per_short_string = maximum_length - minimum_length
    if capacity_per_short_string <= 0:
        return None

    short_string_count = ceil(deficit / capacity_per_short_string)
    if short_string_count > string_count:
        return None

    base_deficit = deficit // short_string_count
    extra = deficit % short_string_count
    deficits = (
        [base_deficit + 1] * extra
        + [base_deficit] * (short_string_count - extra)
    )
    short_lengths = [maximum_length - value for value in deficits]
    lengths = (
        [maximum_length] * (string_count - short_string_count)
        + short_lengths
    )
    if min(lengths) < minimum_length:
        return None
    return lengths


def _enumerate_deficit_partitions(
    total_deficit: int,
    maximum_deficit: int,
    maximum_parts: int,
    *,
    limit: int = 6000,
) -> list[list[int]]:
    """
    Devuelve particiones no crecientes del déficit total. Cada parte positiva
    representa cuántos módulos se restan a un string respecto a la longitud
    máxima. Los strings no incluidos en la partición permanecen al máximo.
    """
    results: list[list[int]] = []

    def visit(
        remaining: int,
        largest_allowed: int,
        parts_left: int,
        prefix: list[int],
    ) -> None:
        if len(results) >= limit:
            return
        if remaining == 0:
            results.append(prefix.copy())
            return
        if parts_left == 0:
            return

        upper = min(largest_allowed, maximum_deficit, remaining)
        lower = max(1, ceil(remaining / parts_left))
        for value in range(upper, lower - 1, -1):
            prefix.append(value)
            visit(
                remaining - value,
                value,
                parts_left - 1,
                prefix,
            )
            prefix.pop()
            if len(results) >= limit:
                return

    if total_deficit == 0:
        return [[]]

    visit(
        total_deficit,
        maximum_deficit,
        maximum_parts,
        [],
    )
    return results


@lru_cache(maxsize=256)
def _candidate_distributions(
    total_modules: int,
    string_count: int,
    minimum_length: int,
    maximum_length: int,
) -> list[dict]:
    candidates: dict[tuple[int, ...], dict] = {}

    def add(lengths: list[int] | None, origin: str) -> None:
        if not lengths:
            return
        if len(lengths) != string_count:
            return
        if sum(lengths) != total_modules:
            return
        if min(lengths) < minimum_length or max(lengths) > maximum_length:
            return

        key = tuple(sorted(lengths, reverse=True))
        if key not in candidates:
            distribution = _distribution_from_lengths(list(key))
            distribution["origins"] = [origin]
            candidates[key] = distribution
        elif origin not in candidates[key]["origins"]:
            candidates[key]["origins"].append(origin)

    add(
        _balanced_lengths(
            total_modules,
            string_count,
            minimum_length,
            maximum_length,
        ),
        "equilibrada",
    )
    add(
        _maximum_voltage_lengths(
            total_modules,
            string_count,
            minimum_length,
            maximum_length,
        ),
        "máximo número de strings a tensión alta",
    )

    if total_modules % string_count == 0:
        uniform_length = total_modules // string_count
        if minimum_length <= uniform_length <= maximum_length:
            add(
                [uniform_length] * string_count,
                "uniforme",
            )

    total_deficit = string_count * maximum_length - total_modules
    maximum_deficit = maximum_length - minimum_length

    for partition in _enumerate_deficit_partitions(
        total_deficit,
        maximum_deficit,
        string_count,
    ):
        lengths = (
            [maximum_length - value for value in partition]
            + [maximum_length] * (string_count - len(partition))
        )
        add(lengths, "combinación válida")

    return list(candidates.values())


def _build_mppt_groups(
    distribution: dict,
    maximum_parallel_strings: int,
) -> list[dict]:
    groups: list[dict] = []

    for item in distribution["lengths"]:
        length = item["modules_per_string"]
        remaining = item["string_count"]

        while remaining > 0:
            parallel = min(maximum_parallel_strings, remaining)
            groups.append({
                "modules_per_string": length,
                "parallel_strings": parallel,
                "total_modules": length * parallel,
            })
            remaining -= parallel

    groups.sort(
        key=lambda group: (
            -group["total_modules"],
            -group["modules_per_string"],
            -group["parallel_strings"],
        )
    )
    return groups


def _assign_groups_to_inverters(
    groups: list[dict],
    inverter_count: int,
    mppt_count: int,
    module_power_w: float,
) -> dict:
    inverters = [
        {
            "inverter_number": index + 1,
            "total_modules": 0,
            "total_strings": 0,
            "mppts": [],
        }
        for index in range(inverter_count)
    ]

    for group in groups:
        available = [
            inverter
            for inverter in inverters
            if len(inverter["mppts"]) < mppt_count
        ]
        if not available:
            raise ValueError(
                "No hay suficientes MPPT para asignar todos los grupos."
            )

        target = min(
            available,
            key=lambda inverter: (
                inverter["total_modules"],
                inverter["total_strings"],
                len(inverter["mppts"]),
                inverter["inverter_number"],
            ),
        )

        target["mppts"].append({
            "mppt_number": 0,
            "modules_per_string": group["modules_per_string"],
            "parallel_strings": group["parallel_strings"],
            "total_modules": group["total_modules"],
        })
        target["total_modules"] += group["total_modules"]
        target["total_strings"] += group["parallel_strings"]

    for inverter in inverters:
        inverter["mppts"].sort(
            key=lambda mppt: (
                -mppt["modules_per_string"],
                -mppt["parallel_strings"],
            )
        )
        for index, mppt in enumerate(inverter["mppts"], start=1):
            mppt["mppt_number"] = index

        inverter["occupied_mppts"] = len(inverter["mppts"])
        inverter["free_mppts"] = mppt_count - len(inverter["mppts"])
        inverter["dc_power_kw"] = (
            inverter["total_modules"] * module_power_w / 1000.0
        )

    module_totals = [item["total_modules"] for item in inverters]
    string_totals = [item["total_strings"] for item in inverters]

    return {
        "inverters": inverters,
        "module_imbalance": max(module_totals) - min(module_totals),
        "string_imbalance": max(string_totals) - min(string_totals),
    }


def _categorise_candidates(candidates: list[dict]) -> None:
    by_string_count: dict[int, list[dict]] = {}
    for candidate in candidates:
        by_string_count.setdefault(
            candidate["strings"],
            [],
        ).append(candidate)

    for same_count in by_string_count.values():
        minimum_spread = min(
            item["distribution"]["spread"]
            for item in same_count
        )
        maximum_max_length_count = max(
            item["distribution"]["maximum_length_count"]
            for item in same_count
        )
        minimum_mppts = min(
            item["occupied_mppts"]
            for item in same_count
        )
        minimum_module_imbalance = min(
            item["mppt_layout"]["module_imbalance"]
            for item in same_count
        )

        for candidate in same_count:
            tags: list[str] = []
            distribution = candidate["distribution"]

            if distribution["distinct_lengths"] == 1:
                tags.append("Strings uniformes")
            if distribution["spread"] == minimum_spread:
                tags.append("Distribución equilibrada")
            if (
                distribution["maximum_length_count"]
                == maximum_max_length_count
            ):
                tags.append("Máximo número a tensión alta")
            if candidate["occupied_mppts"] == minimum_mppts:
                tags.append("Mejor ocupación MPPT")
            if (
                candidate["mppt_layout"]["module_imbalance"]
                == minimum_module_imbalance
            ):
                tags.append("Inversores equilibrados")

            candidate["strategy_tags"] = tags


def _select_diverse_alternatives(
    candidates: list[dict],
    *,
    maximum: int = 10,
) -> list[dict]:
    if not candidates:
        return []

    selected: list[dict] = []
    seen: set[str] = set()

    def add(candidate: dict | None) -> None:
        if not candidate:
            return
        key = candidate["distribution"]["label"] + (
            f"|{candidate['strings']}"
        )
        if key in seen:
            return
        selected.append(candidate)
        seen.add(key)

    add(candidates[0])

    minimum_strings = candidates[0]["strings"]
    same_minimum = [
        item
        for item in candidates
        if item["strings"] == minimum_strings
    ]

    add(min(
        same_minimum,
        key=lambda item: (
            -item["distribution"]["maximum_length_count"],
            item["distribution"]["spread"],
            -item["distribution"]["minimum_length"],
        ),
    ))
    add(min(
        same_minimum,
        key=lambda item: (
            item["occupied_mppts"],
            item["mppt_layout"]["module_imbalance"],
            item["distribution"]["spread"],
        ),
    ))

    uniform = [
        item
        for item in candidates
        if item["distribution"]["distinct_lengths"] == 1
    ]
    if uniform:
        add(min(
            uniform,
            key=lambda item: (
                item["strings"],
                -item["distribution"]["minimum_length"],
            ),
        ))

    for candidate in candidates:
        add(candidate)
        if len(selected) >= maximum:
            break

    return selected[:maximum]


def calculate_cable(
    *,
    current_a: float,
    operating_voltage_v: float,
    string_count: int,
    cable: CableInput,
) -> dict:
    _validate_positive("La longitud del cable", cable.one_way_length_m)
    _validate_positive("La sección del cable", cable.selected_section_mm2)
    _validate_positive("La tensión de funcionamiento", operating_voltage_v)
    _validate_positive(
        "La caída máxima permitida",
        cable.maximum_voltage_drop_pct,
    )

    if cable.material not in {"copper", "aluminium"}:
        raise ValueError("El material debe ser cobre o aluminio.")
    if not -20 <= cable.conductor_temperature_c <= 120:
        raise ValueError(
            "La temperatura del conductor debe estar entre -20 y 120 °C."
        )

    if cable.material == "copper":
        rho_20 = 0.0175
        alpha = 0.00393
    else:
        rho_20 = 0.0282
        alpha = 0.00403

    resistivity = rho_20 * (
        1 + alpha * (cable.conductor_temperature_c - 20.0)
    )

    voltage_drop_v = (
        2
        * cable.one_way_length_m
        * current_a
        * resistivity
        / cable.selected_section_mm2
    )
    voltage_drop_pct = voltage_drop_v / operating_voltage_v * 100.0
    loss_per_string_w = voltage_drop_v * current_a
    total_loss_w = loss_per_string_w * string_count

    minimum_section_mm2 = (
        2
        * cable.one_way_length_m
        * current_a
        * resistivity
        / (
            operating_voltage_v
            * cable.maximum_voltage_drop_pct
            / 100.0
        )
    )

    standard_sections = [2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120]
    recommended = next(
        (
            section
            for section in standard_sections
            if section >= minimum_section_mm2
        ),
        None,
    )

    return {
        "material": cable.material,
        "conductor_temperature_c": cable.conductor_temperature_c,
        "resistivity_ohm_mm2_m": resistivity,
        "voltage_drop_v": voltage_drop_v,
        "voltage_drop_pct": voltage_drop_pct,
        "loss_per_string_w": loss_per_string_w,
        "total_loss_w": total_loss_w,
        "minimum_section_mm2": minimum_section_mm2,
        "recommended_standard_section_mm2": recommended,
        "selected_section_complies": (
            voltage_drop_pct <= cable.maximum_voltage_drop_pct
        ),
        "total_conductor_length_m": (
            2 * cable.one_way_length_m * string_count
        ),
    }


def calculate_dc(
    module: ModuleData,
    inverter: InverterData,
    data: CalculationInput,
) -> dict:
    if data.total_modules <= 0:
        raise ValueError("El número total de módulos debe ser positivo.")
    if data.tmin_c > data.tmax_cell_c:
        raise ValueError(
            "La temperatura mínima no puede ser superior a la máxima de célula."
        )
    if not 0 <= data.margin_pct < 100:
        raise ValueError("El margen debe estar entre 0 % y 100 %.")
    if not 0 <= data.bifacial_gain_pct <= 100:
        raise ValueError("La ganancia bifacial debe estar entre 0 % y 100 %.")

    for name, value in (
        ("Pmax", module.pmax_w),
        ("Voc", module.voc_v),
        ("Vmp", module.vmp_v),
        ("Isc", module.isc_a),
        ("Imp", module.imp_a),
        ("Potencia AC", inverter.pac_w),
        ("Vdc máxima", inverter.max_dc_voltage_v),
        ("MPPT mínimo", inverter.mppt_min_v),
        ("MPPT máximo", inverter.mppt_max_v),
        ("Corriente máxima por MPPT", inverter.max_current_per_mppt_a),
        ("Corriente máxima por string", inverter.max_current_per_string_a),
        (
            "Corriente de cortocircuito máxima por MPPT",
            inverter.max_short_circuit_per_mppt_a,
        ),
    ):
        _validate_positive(name, float(value))

    if inverter.mppt_count <= 0 or inverter.inputs_per_mppt <= 0:
        raise ValueError("El número de MPPT y entradas debe ser positivo.")
    if inverter.mppt_min_v >= inverter.mppt_max_v:
        raise ValueError("El rango MPPT del inversor no es válido.")
    if inverter.mppt_max_v > inverter.max_dc_voltage_v:
        raise ValueError(
            "El límite superior MPPT no puede superar la Vdc máxima absoluta."
        )

    warnings: list[str] = []
    if module.beta_voc_pct_c >= 0:
        warnings.append(
            "βVoc no es negativo. Confirma el signo indicado en el datasheet."
        )
    if module.beta_vmp_pct_c >= 0:
        warnings.append(
            "βVmp no es negativo. Confirma el signo indicado en el datasheet."
        )

    voc_cold = voltage_at_temperature(
        module.voc_v,
        module.beta_voc_pct_c,
        data.tmin_c,
    )
    vmp_cold = voltage_at_temperature(
        module.vmp_v,
        module.beta_vmp_pct_c,
        data.tmin_c,
    )
    vmp_hot = voltage_at_temperature(
        module.vmp_v,
        module.beta_vmp_pct_c,
        data.tmax_cell_c,
    )

    if min(voc_cold, vmp_cold, vmp_hot) <= 0:
        raise ValueError("La corrección térmica produce una tensión no válida.")

    design_limit_v = inverter.max_dc_voltage_v * (
        1 - data.margin_pct / 100.0
    )

    minimum_modules_by_mppt = max(
        1,
        ceil(inverter.mppt_min_v / vmp_hot),
    )
    maximum_modules_by_voc = floor(design_limit_v / voc_cold)
    maximum_modules_by_mppt = floor(
        inverter.mppt_max_v / vmp_cold
    )
    maximum_modules = min(
        maximum_modules_by_voc,
        maximum_modules_by_mppt,
    )

    if maximum_modules < 1:
        raise ValueError(
            "Un solo módulo supera el límite de tensión aplicable."
        )
    if minimum_modules_by_mppt > maximum_modules:
        raise ValueError(
            "No existe una longitud que cumpla simultáneamente Voc y rango MPPT."
        )

    if maximum_modules_by_voc < maximum_modules_by_mppt:
        limiting_constraint = "Voc máxima con margen preventivo"
    elif maximum_modules_by_mppt < maximum_modules_by_voc:
        limiting_constraint = "límite superior del rango MPPT"
    else:
        limiting_constraint = "Voc y rango MPPT"

    bifacial_factor = 1 + data.bifacial_gain_pct / 100.0
    imp_corrected = module.imp_a * bifacial_factor
    isc_corrected = module.isc_a * bifacial_factor

    if imp_corrected > inverter.max_current_per_string_a:
        raise ValueError(
            "Imp corregida supera la corriente máxima por entrada/string."
        )

    by_imp = floor(
        inverter.max_current_per_mppt_a / imp_corrected
    )
    by_isc = floor(
        inverter.max_short_circuit_per_mppt_a / isc_corrected
    )
    possible_parallel_strings = min(
        inverter.inputs_per_mppt,
        by_imp,
        by_isc,
    )
    if possible_parallel_strings < 1:
        raise ValueError(
            "La corriente del módulo no es compatible con un MPPT."
        )

    maximum_parallel_strings = (
        1 if data.one_string_per_mppt else possible_parallel_strings
    )

    minimum_string_count = ceil(
        data.total_modules / maximum_modules
    )
    maximum_string_count = floor(
        data.total_modules / minimum_modules_by_mppt
    )

    # Se estudia primero el mínimo teórico y después algunas configuraciones
    # adicionales para ofrecer opciones uniformes o de mejor uso de MPPT.
    last_string_count = min(
        maximum_string_count,
        minimum_string_count + 8,
    )

    candidates: list[dict] = []

    for string_count in range(
        minimum_string_count,
        last_string_count + 1,
    ):
        distributions = _candidate_distributions(
            data.total_modules,
            string_count,
            minimum_modules_by_mppt,
            maximum_modules,
        )

        for distribution in distributions:
            groups = _build_mppt_groups(
                distribution,
                maximum_parallel_strings,
            )
            occupied_mppts = len(groups)
            inverter_count = ceil(
                occupied_mppts / inverter.mppt_count
            )
            available_mppts = inverter_count * inverter.mppt_count

            layout = _assign_groups_to_inverters(
                groups,
                inverter_count,
                inverter.mppt_count,
                module.pmax_w,
            )

            longest = distribution["maximum_length"]
            shortest = distribution["minimum_length"]

            voc_string_cold = voc_cold * longest
            vmp_string_cold_max = vmp_cold * longest
            vmp_string_hot_min = vmp_hot * shortest

            warnings_for_candidate: list[str] = []
            if voc_string_cold > design_limit_v:
                warnings_for_candidate.append(
                    "Supera el límite preventivo de Voc."
                )
            if voc_string_cold > inverter.max_dc_voltage_v:
                warnings_for_candidate.append(
                    "Supera la tensión DC máxima absoluta."
                )
            if vmp_string_hot_min < inverter.mppt_min_v:
                warnings_for_candidate.append(
                    "Vmp caliente queda por debajo del MPPT."
                )
            if vmp_string_cold_max > inverter.mppt_max_v:
                warnings_for_candidate.append(
                    "Vmp fría supera el límite superior MPPT."
                )

            # Cada MPPT contiene únicamente strings de la misma longitud.
            for inverter_layout in layout["inverters"]:
                for mppt in inverter_layout["mppts"]:
                    if (
                        imp_corrected * mppt["parallel_strings"]
                        > inverter.max_current_per_mppt_a
                    ):
                        warnings_for_candidate.append(
                            "Imp supera la corriente máxima del MPPT."
                        )
                    if (
                        isc_corrected * mppt["parallel_strings"]
                        > inverter.max_short_circuit_per_mppt_a
                    ):
                        warnings_for_candidate.append(
                            "Isc supera la corriente de cortocircuito del MPPT."
                        )

            dc_kw = data.total_modules * module.pmax_w / 1000.0
            ac_kw = inverter_count * inverter.pac_w / 1000.0

            candidates.append({
                "distribution": distribution,
                "strings": string_count,
                "inverter_count": inverter_count,
                "maximum_parallel_strings_per_mppt": (
                    maximum_parallel_strings
                ),
                "occupied_mppts": occupied_mppts,
                "available_mppts": available_mppts,
                "free_mppts": available_mppts - occupied_mppts,
                "voc_string_cold_v": voc_string_cold,
                "vmp_string_cold_max_v": vmp_string_cold_max,
                "vmp_string_hot_min_v": vmp_string_hot_min,
                "average_voltage_utilisation_pct": (
                    distribution["average_modules_per_string"]
                    / maximum_modules
                    * 100.0
                ),
                "dc_ac_ratio": dc_kw / ac_kw,
                "mppt_layout": layout,
                "warnings": sorted(set(warnings_for_candidate)),
            })

    valid_candidates = [
        candidate
        for candidate in candidates
        if not candidate["warnings"]
    ]
    if not valid_candidates:
        raise ValueError(
            "No se ha encontrado una configuración técnicamente válida."
        )

    _categorise_candidates(valid_candidates)

    # Orden estricto:
    # 1) mínimo número de strings;
    # 2) menor diferencia entre longitudes;
    # 3) mayor longitud mínima;
    # 4) menos longitudes diferentes;
    # 5) mejor equilibrio entre inversores;
    # 6) menor ocupación MPPT;
    # 7) más strings a la longitud máxima.
    valid_candidates.sort(
        key=lambda item: (
            item["strings"],
            item["distribution"]["spread"],
            -item["distribution"]["minimum_length"],
            item["distribution"]["distinct_lengths"],
            item["mppt_layout"]["module_imbalance"],
            item["mppt_layout"]["string_imbalance"],
            item["occupied_mppts"],
            -item["distribution"]["maximum_length_count"],
            item["distribution"]["label"],
        )
    )

    recommended = valid_candidates[0]
    recommended["strategy_tags"] = [
        "Recomendada",
        *[
            tag
            for tag in recommended["strategy_tags"]
            if tag != "Recomendada"
        ],
    ]

    alternatives = _select_diverse_alternatives(
        valid_candidates,
        maximum=10,
    )

    superior_modules = maximum_modules + 1
    superior_voc = superior_modules * voc_cold
    superior_vmp_cold = superior_modules * vmp_cold
    superior_reasons: list[str] = []
    if superior_voc > design_limit_v:
        superior_reasons.append(
            "supera el límite preventivo de Voc"
        )
    if superior_voc > inverter.max_dc_voltage_v:
        superior_reasons.append(
            "supera la Vdc máxima absoluta"
        )
    if superior_vmp_cold > inverter.mppt_max_v:
        superior_reasons.append(
            "supera el límite superior MPPT en frío"
        )

    cable_result = None
    if data.cable:
        cable_result = calculate_cable(
            current_a=imp_corrected,
            operating_voltage_v=(
                recommended["vmp_string_hot_min_v"]
            ),
            string_count=recommended["strings"],
            cable=data.cable,
        )

    return {
        "module": asdict(module),
        "inverter": asdict(inverter),
        "input": asdict(data),
        "warnings": warnings,
        "voc_module_cold_v": voc_cold,
        "vmp_module_cold_v": vmp_cold,
        "vmp_module_hot_v": vmp_hot,
        "design_limit_v": design_limit_v,
        "minimum_modules_per_string": minimum_modules_by_mppt,
        "maximum_modules_by_voc": maximum_modules_by_voc,
        "maximum_modules_by_mppt": maximum_modules_by_mppt,
        "maximum_modules_per_string": maximum_modules,
        "minimum_theoretical_strings": minimum_string_count,
        "limiting_constraint": limiting_constraint,
        "superior_configuration": {
            "modules_per_string": superior_modules,
            "voc_v": superior_voc,
            "vmp_cold_v": superior_vmp_cold,
            "is_valid": not superior_reasons,
            "reasons": superior_reasons,
        },
        "imp_corrected_a": imp_corrected,
        "isc_corrected_a": isc_corrected,
        "possible_parallel_strings_per_mppt": (
            possible_parallel_strings
        ),
        "recommended": recommended,
        "alternatives": alternatives,
        "cable": cable_result,
        "optimizer_rules": [
            "No se mezclan strings de distinta longitud en un mismo MPPT.",
            "Se minimiza primero el número total de strings.",
            "Con el mismo número de strings se prioriza la distribución más equilibrada y próxima a la longitud máxima.",
            "Los grupos MPPT se reparten entre inversores buscando equilibrio de módulos y strings.",
            "Las alternativas de máxima tensión, ocupación MPPT y strings uniformes se muestran por separado.",
        ],
    }
