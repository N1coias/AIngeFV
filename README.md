# AIngeFV v1.0.3 — optimizador inteligente de seriados

Base revisada para dimensionamiento de la parte continua de instalaciones
fotovoltaicas, con frontend React, API FastAPI y motor de cálculo independiente.

## Correcciones principales de esta revisión

* La Voc en frío se compara con la tensión DC máxima absoluta del inversor.
* La Vmp se comprueba en sus dos extremos:

  * Vmp mínima con célula caliente.
  * Vmp máxima con célula fría.
* El máximo de módulos se desglosa en:

  * límite por Voc,
  * límite por rango MPPT,
  * límite final aplicado.
* Se mantiene el caso de referencia:

  * 18 módulos válidos,
  * 19 módulos no válidos con margen preventivo del 2 %.
* Los strings de distinta longitud no se mezclan en paralelo sobre un mismo MPPT.
* La bifacialidad modifica Imp e Isc, pero no la Voc.
* El cable DC incorpora corrección de resistividad por temperatura del conductor.
* Se muestran pérdidas por string y pérdidas totales estimadas.
* El lector de módulos ofrece todas las variantes detectadas y exige seleccionar
el modelo/potencia exacto antes de aplicarlo.
* El lector de inversores interpreta potencias expresadas en W o kW.
* Se guardan metadatos de trazabilidad del datasheet:
nombre del archivo y hash SHA-256.
* Se añaden botones de actualización, guardado de equipos y guardado de proyecto.
* El frontend cancela cálculos anteriores para evitar resultados desactualizados.
* Render utiliza Docker con el contexto completo del repositorio.
* El Blueprint incluye servicio web, comprobación de salud y PostgreSQL de prueba.
* Se amplían las pruebas del motor, API y parser de datasheets.

## Estructura

```text
AIngeFV/
├── frontend/
├── backend/
├── engine/
├── tests/
├── docs/
├── render.yaml
└── .github/workflows/tests.yml
```

## Render

La forma más sencilla es crear un **Blueprint** desde el `render.yaml`.

Configuración equivalente manual:

* Runtime: Docker
* Root Directory: vacío
* Dockerfile: `backend/Dockerfile`
* Health Check Path: `/api/health`

El servicio escucha el puerto indicado por la variable `PORT`.

El PostgreSQL gratuito de Render es útil para pruebas, pero actualmente expira
tras 30 días. Para conservar datos de forma estable se necesita un plan de base
de datos persistente.

## Vercel

* Root Directory: `frontend`
* Framework: Vite
* Build Command: `npm run build`
* Output Directory: `dist`

Variable obligatoria:

```text
VITE\_API\_URL=https://TU-API.onrender.com
```

Después de crear o modificar la variable hay que volver a desplegar el proyecto.

## Advertencia del lector PDF

La lectura combina texto, tablas y OCR. Los datos detectados no se consideran
válidos hasta que el usuario selecciona la variante exacta, revisa los campos y
los guarda como confirmados.



## Núcleo de esta versión: seriados inteligentes

La v1.0.3 incorpora un optimizador específico que:

* minimiza primero el número total de strings;
* prioriza longitudes próximas al máximo permitido;
* no mezcla strings con distinto número de módulos en un mismo MPPT;
* genera múltiples distribuciones válidas;
* asigna cada grupo a un MPPT concreto;
* equilibra módulos y strings entre inversores;
* presenta alternativas equilibradas, de máxima tensión, de mejor ocupación MPPT
y uniformes.

Para el caso de 210 módulos y máximo de 18 módulos/string, la recomendación es:

```text
6×18 + 6×17 = 210 módulos
12 strings totales
```

La alternativa `11×18 + 1×12` aparece como opción de máxima cantidad de strings a
18 módulos, pero no supera a la distribución equilibrada.

Despliegue Vercel v1.0.3

