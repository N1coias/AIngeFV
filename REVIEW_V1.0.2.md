# Revisión técnica v1.0.1

## Regla de tensión

La Voc corregida en frío se compara con la tensión DC máxima absoluta del inversor.
El rango MPPT se utiliza para la Vmp de funcionamiento.

## Coeficientes

No se utiliza automáticamente γPmax como si fuera βVmp. El cálculo exige un coeficiente específico
de Vmp o un valor manual técnicamente justificado.

## Bifacialidad

La ganancia bifacial modifica Imp e Isc. No modifica directamente el límite de Voc.

## Datasheets

El lector tiene tres fases:

1. extracción de texto,
2. extracción de tablas,
3. OCR si no hay texto suficiente.

Los datos quedan pendientes de confirmación. No se guardan automáticamente como válidos.

## Despliegue

Render utiliza Docker con contexto del repositorio completo para que el backend tenga acceso al motor
independiente situado en `engine/`.
