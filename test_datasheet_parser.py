import React, {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API = (
  import.meta.env.VITE_API_URL || "http://localhost:8000"
).replace(/\/+$/, "");

type ModuleVariant = {
  manufacturer: string;
  family: string;
  model: string;
  pmax_w: number;
  voc_v: number;
  vmp_v: number;
  isc_a: number;
  imp_a: number;
};

type ModuleRead = {
  source_filename: string;
  datasheet_sha256: string;
  variants: ModuleVariant[];
  beta_voc_pct_c: number | null;
  beta_vmp_pct_c: number | null;
  confidence: number;
  warnings: string[];
};

type InverterCandidate = {
  manufacturer: string;
  model: string;
  pac_w: number | null;
  max_dc_voltage_v: number | null;
  mppt_min_v: number | null;
  mppt_max_v: number | null;
  mppt_count: number | null;
  inputs_per_mppt: number | null;
  max_current_per_mppt_a: number | null;
  max_current_per_string_a: number | null;
  max_short_circuit_per_mppt_a: number | null;
};

type InverterRead = {
  source_filename: string;
  datasheet_sha256: string;
  inverter: InverterCandidate;
  confidence: number;
  warnings: string[];
};


type MpptAssignment = {
  mppt_number: number;
  modules_per_string: number;
  parallel_strings: number;
  total_modules: number;
};

type InverterLayout = {
  inverter_number: number;
  total_modules: number;
  total_strings: number;
  occupied_mppts: number;
  free_mppts: number;
  dc_power_kw: number;
  mppts: MpptAssignment[];
};

type Alternative = {
  distribution: {
    label: string;
    minimum_length: number;
    maximum_length: number;
    spread: number;
    distinct_lengths: number;
    maximum_length_count: number;
    average_modules_per_string: number;
    lengths: Array<{
      modules_per_string: number;
      string_count: number;
    }>;
  };
  strings: number;
  inverter_count: number;
  maximum_parallel_strings_per_mppt: number;
  occupied_mppts: number;
  available_mppts: number;
  free_mppts: number;
  voc_string_cold_v: number;
  vmp_string_cold_max_v: number;
  vmp_string_hot_min_v: number;
  average_voltage_utilisation_pct: number;
  dc_ac_ratio: number;
  strategy_tags: string[];
  mppt_layout: {
    module_imbalance: number;
    string_imbalance: number;
    inverters: InverterLayout[];
  };
  warnings: string[];
};

type Result = {
  warnings: string[];
  optimizer_rules: string[];
  voc_module_cold_v: number;
  vmp_module_cold_v: number;
  vmp_module_hot_v: number;
  design_limit_v: number;
  minimum_modules_per_string: number;
  maximum_modules_by_voc: number;
  maximum_modules_by_mppt: number;
  maximum_modules_per_string: number;
  minimum_theoretical_strings: number;
  limiting_constraint: string;
  superior_configuration: {
    modules_per_string: number;
    voc_v: number;
    vmp_cold_v: number;
    is_valid: boolean;
    reasons: string[];
  };
  imp_corrected_a: number;
  isc_corrected_a: number;
  possible_parallel_strings_per_mppt: number;
  recommended: Alternative;
  alternatives: Alternative[];
  cable: null | {
    voltage_drop_pct: number;
    loss_per_string_w: number;
    total_loss_w: number;
    minimum_section_mm2: number;
    recommended_standard_section_mm2: number | null;
    selected_section_complies: boolean;
    total_conductor_length_m: number;
  };
};

function NumberField(props: {
  label: string;
  value: number;
  step?: number;
  onChange: (value: number) => void;
}) {
  return (
    <label>
      {props.label}
      <input
        type="number"
        value={props.value}
        step={props.step}
        onChange={(event) => {
          const value = Number(event.target.value);
          if (Number.isFinite(value)) props.onChange(value);
        }}
      />
    </label>
  );
}

async function jsonRequest(
  path: string,
  options: RequestInit = {},
) {
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  const text = await response.text();
  let data: any = {};
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { detail: text };
    }
  }

  if (!response.ok) {
    throw new Error(data.detail || `Error HTTP ${response.status}`);
  }
  return data;
}

function App() {
  const [apiStatus, setApiStatus] = useState("Comprobando…");
  const [refreshToken, setRefreshToken] = useState(0);

  const [projectName, setProjectName] = useState("Proyecto DC");
  const [client, setClient] = useState("");
  const [location, setLocation] = useState("");
  const [roofType, setRoofType] = useState("");

  const [moduleManufacturer, setModuleManufacturer] = useState("JA Solar");
  const [moduleFamily, setModuleFamily] = useState("JAM72D40");
  const [moduleModel, setModuleModel] = useState("Módulo manual");
  const [moduleSource, setModuleSource] = useState("");
  const [moduleHash, setModuleHash] = useState("");
  const [moduleRead, setModuleRead] = useState<ModuleRead | null>(null);
  const [selectedVariant, setSelectedVariant] = useState(0);
  const [moduleStatus, setModuleStatus] = useState("Sin datasheet.");
  const [pmax, setPmax] = useState(595);
  const [voc, setVoc] = useState(52.58);
  const [vmp, setVmp] = useState(44.64);
  const [isc, setIsc] = useState(13.99);
  const [imp, setImp] = useState(13.33);
  const [betaVoc, setBetaVoc] = useState(-0.260);
  const [betaVmp, setBetaVmp] = useState(-0.290);

  const [inverterManufacturer, setInverterManufacturer] = useState("Huawei");
  const [inverterModel, setInverterModel] = useState("SUN2000-100KTL-M2");
  const [inverterSource, setInverterSource] = useState("");
  const [inverterHash, setInverterHash] = useState("");
  const [inverterRead, setInverterRead] = useState<InverterRead | null>(null);
  const [inverterStatus, setInverterStatus] = useState("Sin datasheet.");
  const [pac, setPac] = useState(100000);
  const [maxDc, setMaxDc] = useState(1100);
  const [mpptMin, setMpptMin] = useState(200);
  const [mpptMax, setMpptMax] = useState(1000);
  const [mpptCount, setMpptCount] = useState(10);
  const [inputsPerMppt, setInputsPerMppt] = useState(2);
  const [maxCurrentMppt, setMaxCurrentMppt] = useState(30);
  const [maxCurrentString, setMaxCurrentString] = useState(20);
  const [maxIscMppt, setMaxIscMppt] = useState(40);

  const [totalModules, setTotalModules] = useState(210);
  const [tmin, setTmin] = useState(-10);
  const [tmax, setTmax] = useState(70);
  const [margin, setMargin] = useState(2);
  const [bifacialGain, setBifacialGain] = useState(0);
  const [oneStringPerMppt, setOneStringPerMppt] = useState(true);

  const [length, setLength] = useState(35);
  const [material, setMaterial] = useState<"copper" | "aluminium">("copper");
  const [section, setSection] = useState(6);
  const [maximumDrop, setMaximumDrop] = useState(1.5);
  const [conductorTemperature, setConductorTemperature] = useState(70);

  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState("");
  const [projectStatus, setProjectStatus] = useState("Proyecto sin guardar.");

  const calculationAbort = useRef<AbortController | null>(null);

  const modulePayload = useMemo(() => ({
    manufacturer: moduleManufacturer,
    family: moduleFamily,
    model: moduleModel,
    pmax_w: pmax,
    voc_v: voc,
    vmp_v: vmp,
    isc_a: isc,
    imp_a: imp,
    beta_voc_pct_c: betaVoc,
    beta_vmp_pct_c: betaVmp,
    source_filename: moduleSource,
    datasheet_sha256: moduleHash,
    confirmed: true,
  }), [
    moduleManufacturer, moduleFamily, moduleModel, pmax, voc, vmp,
    isc, imp, betaVoc, betaVmp, moduleSource, moduleHash,
  ]);

  const inverterPayload = useMemo(() => ({
    manufacturer: inverterManufacturer,
    model: inverterModel,
    pac_w: pac,
    max_dc_voltage_v: maxDc,
    mppt_min_v: mpptMin,
    mppt_max_v: mpptMax,
    mppt_count: mpptCount,
    inputs_per_mppt: inputsPerMppt,
    max_current_per_mppt_a: maxCurrentMppt,
    max_current_per_string_a: maxCurrentString,
    max_short_circuit_per_mppt_a: maxIscMppt,
    source_filename: inverterSource,
    datasheet_sha256: inverterHash,
    confirmed: true,
  }), [
    inverterManufacturer, inverterModel, pac, maxDc, mpptMin, mpptMax,
    mpptCount, inputsPerMppt, maxCurrentMppt, maxCurrentString,
    maxIscMppt, inverterSource, inverterHash,
  ]);

  const calculationPayload = useMemo(() => ({
    module: modulePayload,
    inverter: inverterPayload,
    total_modules: totalModules,
    tmin_c: tmin,
    tmax_cell_c: tmax,
    margin_pct: margin,
    bifacial_gain_pct: bifacialGain,
    one_string_per_mppt: oneStringPerMppt,
    cable: {
      one_way_length_m: length,
      material,
      selected_section_mm2: section,
      maximum_voltage_drop_pct: maximumDrop,
      conductor_temperature_c: conductorTemperature,
    },
  }), [
    modulePayload, inverterPayload, totalModules, tmin, tmax, margin,
    bifacialGain, oneStringPerMppt, length, material, section,
    maximumDrop, conductorTemperature,
  ]);

  async function checkApi() {
    setApiStatus("Comprobando…");
    try {
      const response = await fetch(`${API}/api/health`, {
        cache: "no-store",
      });
      if (!response.ok) throw new Error("API no disponible");
      const data = await response.json();
      setApiStatus(`Conectada · v${data.version}`);
    } catch {
      setApiStatus("Sin conexión");
    }
  }

  useEffect(() => {
    checkApi();
  }, []);

  useEffect(() => {
    calculationAbort.current?.abort();
    const controller = new AbortController();
    calculationAbort.current = controller;

    const timer = window.setTimeout(async () => {
      setError("");
      try {
        const response = await fetch(`${API}/api/calculate/dc`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(calculationPayload),
          signal: controller.signal,
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || "Error de cálculo");
        }
        setResult(data);
      } catch (problem) {
        if (
          problem instanceof DOMException
          && problem.name === "AbortError"
        ) return;

        setResult(null);
        setError(
          problem instanceof Error
            ? problem.message
            : "Error de conexión",
        );
      }
    }, 300);

    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [calculationPayload, refreshToken]);

  async function upload(
    file: File,
    kind: "module" | "inverter",
  ) {
    if (file.size > 20 * 1024 * 1024) {
      throw new Error("El archivo supera 20 MB.");
    }

    const form = new FormData();
    form.append("file", file);

    const response = await fetch(`${API}/api/datasheet/${kind}`, {
      method: "POST",
      body: form,
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(
        data.detail || "No se ha podido analizar el archivo",
      );
    }
    return data;
  }

  function applyModuleVariant() {
    if (!moduleRead?.variants.length) return;
    const variant = moduleRead.variants[selectedVariant];
    setModuleManufacturer(variant.manufacturer || "");
    setModuleFamily(variant.family || "");
    setModuleModel(variant.model);
    setPmax(Number(variant.pmax_w));
    setVoc(Number(variant.voc_v));
    setVmp(Number(variant.vmp_v));
    setIsc(Number(variant.isc_a));
    setImp(Number(variant.imp_a));
    if (moduleRead.beta_voc_pct_c != null) {
      setBetaVoc(Number(moduleRead.beta_voc_pct_c));
    }
    if (moduleRead.beta_vmp_pct_c != null) {
      setBetaVmp(Number(moduleRead.beta_vmp_pct_c));
    }
    setModuleSource(moduleRead.source_filename);
    setModuleHash(moduleRead.datasheet_sha256);
    setModuleStatus("Variante aplicada. Revisa los datos antes de guardar.");
  }

  function applyInverterRead() {
    if (!inverterRead) return;
    const item = inverterRead.inverter;
    if (item.manufacturer) setInverterManufacturer(item.manufacturer);
    if (item.model) setInverterModel(item.model);
    if (item.pac_w != null) setPac(Number(item.pac_w));
    if (item.max_dc_voltage_v != null) setMaxDc(Number(item.max_dc_voltage_v));
    if (item.mppt_min_v != null) setMpptMin(Number(item.mppt_min_v));
    if (item.mppt_max_v != null) setMpptMax(Number(item.mppt_max_v));
    if (item.mppt_count != null) setMpptCount(Number(item.mppt_count));
    if (item.inputs_per_mppt != null) setInputsPerMppt(Number(item.inputs_per_mppt));
    if (item.max_current_per_mppt_a != null) {
      setMaxCurrentMppt(Number(item.max_current_per_mppt_a));
    }
    if (item.max_current_per_string_a != null) {
      setMaxCurrentString(Number(item.max_current_per_string_a));
    }
    if (item.max_short_circuit_per_mppt_a != null) {
      setMaxIscMppt(Number(item.max_short_circuit_per_mppt_a));
    }
    setInverterSource(inverterRead.source_filename);
    setInverterHash(inverterRead.datasheet_sha256);
    setInverterStatus("Datos aplicados. Revisa los campos antes de guardar.");
  }

  const temperatureRows = useMemo(() => {
    const modulesPerString = (
      result?.maximum_modules_per_string || 1
    );
    const rows = [];
    for (let temperature = -20; temperature <= 80; temperature += 10) {
      const vocAtTemperature = voc * (
        1 + (betaVoc / 100) * (temperature - 25)
      );
      const vmpAtTemperature = vmp * (
        1 + (betaVmp / 100) * (temperature - 25)
      );
      rows.push({
        temperature,
        vocModule: vocAtTemperature,
        vocString: vocAtTemperature * modulesPerString,
        vmpModule: vmpAtTemperature,
        vmpString: vmpAtTemperature * modulesPerString,
      });
    }
    return rows;
  }, [voc, vmp, betaVoc, betaVmp, result]);

  return (
    <main>
      <header>
        <div className="logo">☀＋</div>
        <div>
          <h1>AIngeFV</h1>
          <p>Core DC v1.0.3 · optimizador de seriados · API {apiStatus}</p>
        </div>
        <button className="secondary" onClick={checkApi}>
          Comprobar API
        </button>
      </header>

      <section className="card">
        <h2>Proyecto</h2>
        <div className="grid">
          <label>
            Nombre
            <input value={projectName} onChange={(event) => setProjectName(event.target.value)} />
          </label>
          <label>
            Cliente
            <input value={client} onChange={(event) => setClient(event.target.value)} />
          </label>
          <label>
            Ubicación
            <input value={location} onChange={(event) => setLocation(event.target.value)} />
          </label>
          <label>
            Tipo de cubierta
            <input value={roofType} onChange={(event) => setRoofType(event.target.value)} />
          </label>
        </div>
        <button
          onClick={async () => {
            try {
              const data = await jsonRequest("/api/projects", {
                method: "POST",
                body: JSON.stringify({
                  name: projectName,
                  client,
                  location,
                  roof_type: roofType,
                  payload: calculationPayload,
                }),
              });
              setProjectStatus(`Proyecto guardado · ID ${data.id}`);
            } catch (problem) {
              setProjectStatus(
                problem instanceof Error ? problem.message : "Error",
              );
            }
          }}
        >
          Guardar proyecto
        </button>
        <span className="status">{projectStatus}</span>
      </section>

      <section className="two">
        <article className="card">
          <h2>Módulo</h2>
          <input
            type="file"
            accept=".pdf,.png,.jpg,.jpeg"
            onChange={async (event) => {
              const file = event.target.files?.[0];
              if (!file) return;
              setModuleStatus("Analizando datasheet…");
              try {
                const data = await upload(file, "module");
                setModuleRead(data);
                setSelectedVariant(0);
                setModuleStatus(
                  `Lectura completada · confianza ${Math.round(
                    (data.confidence || 0) * 100,
                  )} %`,
                );
              } catch (problem) {
                setModuleStatus(
                  problem instanceof Error ? problem.message : "Error",
                );
              }
            }}
          />

          {moduleRead && (
            <div className="reader">
              <p>{moduleRead.warnings.join(" · ")}</p>
              {moduleRead.variants.length > 0 ? (
                <>
                  <label>
                    Variante exacta detectada
                    <select
                      value={selectedVariant}
                      onChange={(event) => setSelectedVariant(
                        Number(event.target.value),
                      )}
                    >
                      {moduleRead.variants.map((variant, index) => (
                        <option key={index} value={index}>
                          {variant.model} · {variant.pmax_w} W · Voc {variant.voc_v} V
                        </option>
                      ))}
                    </select>
                  </label>
                  <button onClick={applyModuleVariant}>
                    Aplicar variante seleccionada
                  </button>
                </>
              ) : (
                <p>No se detectó una variante completa. Introduce los datos manualmente.</p>
              )}
            </div>
          )}

          <span className="status">{moduleStatus}</span>

          <div className="grid">
            <label>
              Fabricante
              <input value={moduleManufacturer} onChange={(event) => setModuleManufacturer(event.target.value)} />
            </label>
            <label>
              Familia
              <input value={moduleFamily} onChange={(event) => setModuleFamily(event.target.value)} />
            </label>
            <label>
              Modelo exacto
              <input value={moduleModel} onChange={(event) => setModuleModel(event.target.value)} />
            </label>
            <NumberField label="Potencia W" value={pmax} onChange={setPmax} />
            <NumberField label="Voc V" value={voc} step={0.01} onChange={setVoc} />
            <NumberField label="Vmp V" value={vmp} step={0.01} onChange={setVmp} />
            <NumberField label="Isc A" value={isc} step={0.01} onChange={setIsc} />
            <NumberField label="Imp A" value={imp} step={0.01} onChange={setImp} />
            <NumberField label="βVoc %/°C" value={betaVoc} step={0.001} onChange={setBetaVoc} />
            <NumberField label="βVmp %/°C" value={betaVmp} step={0.001} onChange={setBetaVmp} />
          </div>

          <button
            onClick={async () => {
              try {
                const data = await jsonRequest("/api/equipment/modules", {
                  method: "POST",
                  body: JSON.stringify(modulePayload),
                });
                setModuleStatus(
                  data.created
                    ? "Módulo guardado en el servidor."
                    : "Módulo existente actualizado.",
                );
              } catch (problem) {
                setModuleStatus(
                  problem instanceof Error ? problem.message : "Error",
                );
              }
            }}
          >
            Guardar módulo confirmado
          </button>
        </article>

        <article className="card">
          <h2>Inversor</h2>
          <input
            type="file"
            accept=".pdf,.png,.jpg,.jpeg"
            onChange={async (event) => {
              const file = event.target.files?.[0];
              if (!file) return;
              setInverterStatus("Analizando datasheet…");
              try {
                const data = await upload(file, "inverter");
                setInverterRead(data);
                setInverterStatus(
                  `Lectura completada · confianza ${Math.round(
                    (data.confidence || 0) * 100,
                  )} %`,
                );
              } catch (problem) {
                setInverterStatus(
                  problem instanceof Error ? problem.message : "Error",
                );
              }
            }}
          />

          {inverterRead && (
            <div className="reader">
              <p>{inverterRead.warnings.join(" · ")}</p>
              <button onClick={applyInverterRead}>
                Aplicar datos detectados
              </button>
            </div>
          )}

          <span className="status">{inverterStatus}</span>

          <div className="grid">
            <label>
              Fabricante
              <input value={inverterManufacturer} onChange={(event) => setInverterManufacturer(event.target.value)} />
            </label>
            <label>
              Modelo exacto
              <input value={inverterModel} onChange={(event) => setInverterModel(event.target.value)} />
            </label>
            <NumberField label="Potencia AC W" value={pac} onChange={setPac} />
            <NumberField label="Vdc máxima V" value={maxDc} onChange={setMaxDc} />
            <NumberField label="MPPT mín. V" value={mpptMin} onChange={setMpptMin} />
            <NumberField label="MPPT máx. V" value={mpptMax} onChange={setMpptMax} />
            <NumberField label="N.º MPPT" value={mpptCount} onChange={setMpptCount} />
            <NumberField label="Entradas/MPPT" value={inputsPerMppt} onChange={setInputsPerMppt} />
            <NumberField label="I máx./MPPT A" value={maxCurrentMppt} onChange={setMaxCurrentMppt} />
            <NumberField label="I máx./string A" value={maxCurrentString} onChange={setMaxCurrentString} />
            <NumberField label="Isc máx./MPPT A" value={maxIscMppt} onChange={setMaxIscMppt} />
          </div>

          <button
            onClick={async () => {
              try {
                const data = await jsonRequest("/api/equipment/inverters", {
                  method: "POST",
                  body: JSON.stringify(inverterPayload),
                });
                setInverterStatus(
                  data.created
                    ? "Inversor guardado en el servidor."
                    : "Inversor existente actualizado.",
                );
              } catch (problem) {
                setInverterStatus(
                  problem instanceof Error ? problem.message : "Error",
                );
              }
            }}
          >
            Guardar inversor confirmado
          </button>
        </article>
      </section>

      <section className="card">
        <div className="title-row">
          <h2>Condiciones y cable DC</h2>
          <button onClick={() => setRefreshToken((value) => value + 1)}>
            Actualizar cálculos
          </button>
        </div>
        <div className="grid">
          <NumberField label="Módulos totales" value={totalModules} onChange={setTotalModules} />
          <NumberField label="Tmín °C" value={tmin} onChange={setTmin} />
          <NumberField label="Tmáx. célula °C" value={tmax} onChange={setTmax} />
          <label>
            Margen preventivo
            <select value={margin} onChange={(event) => setMargin(Number(event.target.value))}>
              <option value={2}>2 %</option>
              <option value={3}>3 %</option>
            </select>
          </label>
          <NumberField label="Ganancia bifacial %" value={bifacialGain} onChange={setBifacialGain} />
          <label>
            Política MPPT
            <select
              value={oneStringPerMppt ? "one" : "multiple"}
              onChange={(event) => setOneStringPerMppt(event.target.value === "one")}
            >
              <option value="one">Priorizar 1 string/MPPT</option>
              <option value="multiple">Permitir paralelos compatibles</option>
            </select>
          </label>
          <NumberField label="Longitud unidireccional m" value={length} onChange={setLength} />
          <label>
            Material
            <select value={material} onChange={(event) => setMaterial(event.target.value as "copper" | "aluminium")}>
              <option value="copper">Cobre</option>
              <option value="aluminium">Aluminio</option>
            </select>
          </label>
          <NumberField label="Sección seleccionada mm²" value={section} onChange={setSection} />
          <NumberField label="Caída máxima %" value={maximumDrop} step={0.1} onChange={setMaximumDrop} />
          <NumberField label="Temperatura conductor °C" value={conductorTemperature} onChange={setConductorTemperature} />
        </div>
      </section>

      {error && <div className="error">{error}</div>}

      {result && (
        <>
          <section className="kpis">
            <div>
              <span>Máximo/string</span>
              <strong>{result.maximum_modules_per_string}</strong>
            </div>
            <div>
              <span>Distribución</span>
              <strong>{result.recommended.distribution.label}</strong>
            </div>
            <div>
              <span>Strings</span>
              <strong>{result.recommended.strings}</strong>
            </div>
            <div>
              <span>Inversores</span>
              <strong>{result.recommended.inverter_count}</strong>
            </div>
          </section>

          <section className="card">
            <h2>Justificación técnica</h2>
            <p>
              Voc corregida a {tmin} °C:
              <b> {result.voc_module_cold_v.toFixed(2)} V/módulo</b>.
            </p>
            <p>
              Límite preventivo:
              <b> {result.design_limit_v.toFixed(2)} V</b>.
            </p>
            <p>
              Máximo por Voc:
              <b> {result.maximum_modules_by_voc}</b> · máximo por MPPT:
              <b> {result.maximum_modules_by_mppt}</b>.
            </p>
            <p>
              Condición limitante:
              <b> {result.limiting_constraint}</b>.
            </p>
            <p>
              String recomendado:
              <b> {result.recommended.voc_string_cold_v.toFixed(2)} V Voc</b>,
              {" "}<b>{result.recommended.vmp_string_cold_max_v.toFixed(2)} V Vmp fría</b>
              {" "}y <b>{result.recommended.vmp_string_hot_min_v.toFixed(2)} V Vmp caliente</b>.
            </p>
            <p>
              Configuración superior:
              <b> {result.superior_configuration.modules_per_string} módulos</b>
              {" "}→ {result.superior_configuration.voc_v.toFixed(2)} V Voc.
              {" "}{result.superior_configuration.is_valid
                ? "Cumple."
                : `No cumple: ${result.superior_configuration.reasons.join(", ")}.`}
            </p>
            <p>
              MPPT ocupados:
              <b> {result.recommended.occupied_mppts}/{result.recommended.available_mppts}</b>,
              {" "}con hasta {result.recommended.maximum_parallel_strings_per_mppt}
              {" "}string(s) iguales por MPPT.
            </p>
            <p>
              Imp corregida:
              <b> {result.imp_corrected_a.toFixed(2)} A</b> · Isc corregida:
              <b> {result.isc_corrected_a.toFixed(2)} A</b>.
            </p>
            {result.warnings.length > 0 && (
              <div className="warning">{result.warnings.join(" · ")}</div>
            )}
            <div className="optimizer-rules">
              <h3>Reglas del optimizador</h3>
              {result.optimizer_rules.map((rule, index) => (
                <p key={index}>✓ {rule}</p>
              ))}
            </div>
          </section>

          <section className="card">
            <h2>Mapa MPPT recomendado</h2>
            <p>
              Cada MPPT contiene exclusivamente strings con el mismo número de módulos.
              La distribución busca equilibrar los módulos entre inversores.
            </p>
            <div className="inverter-grid">
              {result.recommended.mppt_layout.inverters.map((inverter) => (
                <article className="inverter-card" key={inverter.inverter_number}>
                  <h3>Inversor {inverter.inverter_number}</h3>
                  <p>
                    <b>{inverter.total_modules} módulos</b> · {inverter.total_strings} strings ·
                    {" "}{inverter.occupied_mppts} MPPT ocupados · {inverter.free_mppts} libres
                  </p>
                  <div className="mppt-list">
                    {inverter.mppts.map((mppt) => (
                      <div className="mppt-item" key={mppt.mppt_number}>
                        <span>MPPT {mppt.mppt_number}</span>
                        <strong>
                          {mppt.parallel_strings}×{mppt.modules_per_string}
                        </strong>
                        <small>{mppt.total_modules} módulos</small>
                      </div>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          </section>

          {result.cable && (
            <section className="card">
              <h2>Cable DC</h2>
              <div className="kpis compact">
                <div>
                  <span>Caída</span>
                  <strong>{result.cable.voltage_drop_pct.toFixed(2)} %</strong>
                </div>
                <div>
                  <span>Sección mínima</span>
                  <strong>{result.cable.minimum_section_mm2.toFixed(2)} mm²</strong>
                </div>
                <div>
                  <span>Sección recomendada</span>
                  <strong>{result.cable.recommended_standard_section_mm2 ?? ">120"} mm²</strong>
                </div>
                <div>
                  <span>Pérdida total</span>
                  <strong>{result.cable.total_loss_w.toFixed(1)} W</strong>
                </div>
              </div>
              <p>
                Longitud total estimada de conductores:
                <b> {result.cable.total_conductor_length_m.toFixed(0)} m</b>.
              </p>
            </section>
          )}

          <section className="card">
            <h2>Tabla térmica</h2>
            <div className="table">
              <table>
                <thead>
                  <tr>
                    <th>Temperatura</th>
                    <th>Voc módulo</th>
                    <th>Voc string</th>
                    <th>Vmp módulo</th>
                    <th>Vmp string</th>
                  </tr>
                </thead>
                <tbody>
                  {temperatureRows.map((row) => (
                    <tr key={row.temperature}>
                      <td>{row.temperature} °C</td>
                      <td>{row.vocModule.toFixed(2)} V</td>
                      <td>{row.vocString.toFixed(2)} V</td>
                      <td>{row.vmpModule.toFixed(2)} V</td>
                      <td>{row.vmpString.toFixed(2)} V</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="card">
            <h2>Alternativas inteligentes de seriado</h2>
            <p>La primera prioridad es el mínimo número de strings. Después se comparan equilibrio, tensión, MPPT e inversores.</p>
            <div className="table">
              <table>
                <thead>
                  <tr>
                    <th>Estrategia</th>
                    <th>Distribución</th>
                    <th>Strings</th>
                    <th>Inversores</th>
                    <th>MPPT</th>
                    <th>Aprovechamiento tensión</th>
                    <th>Voc frío</th>
                    <th>Vmp fría/caliente</th>
                    <th>DC/AC</th>
                  </tr>
                </thead>
                <tbody>
                  {result.alternatives.map((row, index) => (
                    <tr key={index} className={index === 0 ? "best" : ""}>
                      <td>
                        <div className="tags">
                          {row.strategy_tags.map((tag) => (
                            <span key={tag}>{tag}</span>
                          ))}
                        </div>
                      </td>
                      <td>{row.distribution.label}</td>
                      <td>{row.strings}</td>
                      <td>{row.inverter_count}</td>
                      <td>{row.occupied_mppts}/{row.available_mppts}</td>
                      <td>{row.average_voltage_utilisation_pct.toFixed(1)} %</td>
                      <td>{row.voc_string_cold_v.toFixed(1)} V</td>
                      <td>
                        {row.vmp_string_cold_max_v.toFixed(1)} /
                        {" "}{row.vmp_string_hot_min_v.toFixed(1)} V
                      </td>
                      <td>{row.dc_ac_ratio.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
