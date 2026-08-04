# Optimizador inteligente de seriados — v1.0.3

## Regla innegociable de MPPT

Un MPPT puede recibir uno o varios strings en paralelo únicamente cuando dichos
strings tienen:

- el mismo modelo de módulo;
- el mismo número de módulos;
- la misma orientación y condiciones eléctricas equivalentes.

La aplicación nunca asigna directamente un string de 18 módulos y otro de 17 al
mismo MPPT.

## Orden estricto de decisión

1. Cumplimiento de Voc, Vmp, Imp e Isc.
2. Mínimo número total de strings.
3. Menor diferencia entre la longitud más larga y la más corta.
4. Mayor longitud mínima de string.
5. Menor número de longitudes distintas.
6. Equilibrio de módulos y strings entre inversores.
7. Menor ocupación de MPPT.
8. Mayor número de strings a la longitud máxima.

El primer criterio de optimización es el número de strings. Para 210 módulos y
un máximo de 18 módulos/string:

```text
ceil(210 / 18) = 12 strings
```

Mientras exista una solución válida con 12 strings, una solución de 13 o 14
strings no puede ser la recomendada.

## Alternativas mostradas

La aplicación no se limita a una única distribución. Genera particiones válidas
de módulos y destaca:

- distribución recomendada y equilibrada;
- máximo número de strings a la longitud máxima;
- mejor ocupación de MPPT;
- alternativa uniforme cuando existe;
- otras configuraciones técnicamente válidas.

Ejemplo para 210 módulos:

- 6×18 + 6×17 — recomendada;
- 11×18 + 1×12 — máxima cantidad a 18;
- 14×15 — strings uniformes, pero con más strings.

## Mapa MPPT

Cada alternativa incluye un mapa concreto:

```text
Inversor 1
MPPT 1 → 1×18
MPPT 2 → 1×18
MPPT 3 → 1×18
MPPT 4 → 1×17
MPPT 5 → 1×17
MPPT 6 → 1×17
```

En el modo de paralelos compatibles:

```text
MPPT 1 → 2×18
MPPT 2 → 2×18
MPPT 3 → 2×18
MPPT 4 → 2×17
MPPT 5 → 2×17
MPPT 6 → 2×17
```

Nunca aparece `1×18 + 1×17` dentro de un único MPPT.
