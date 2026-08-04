# Revisión técnica v1.0.2

## 1. Tensión de strings

Se separan dos restricciones distintas:

1. **Voc máxima en frío**
   - Se compara con la Vdc máxima absoluta del inversor.
   - Se aplica el margen preventivo seleccionado.

2. **Vmp máxima en frío**
   - Se compara con el límite superior del rango MPPT.

La longitud máxima final es el menor valor permitido por ambas condiciones.

## 2. Rango MPPT

- El mínimo de módulos se calcula con Vmp a temperatura máxima de célula.
- El máximo operativo por MPPT se calcula con Vmp a temperatura mínima.
- La aplicación muestra qué condición limita el diseño.

## 3. Paralelos por MPPT

Los strings de longitudes distintas se asignan a grupos MPPT diferentes. Nunca se
considera válido paralelizar directamente un string de 17 módulos con otro de 18.

## 4. Bifacialidad

La ganancia bifacial se aplica a Imp e Isc. La Voc no se multiplica por la ganancia
bifacial.

## 5. Cable DC

El cálculo de caída utiliza resistividad corregida según la temperatura del conductor.
Sigue siendo una comprobación preliminar: la intensidad admisible, agrupamiento,
método de instalación y prescripciones completas del REBT/UNE se incorporarán en
una fase posterior.

## 6. Datasheets

La lectura combina:

- extracción de texto,
- extracción de tablas,
- OCR de respaldo,
- detección de variantes,
- metadatos de trazabilidad.

Los resultados necesitan confirmación humana antes de guardarse en la base de datos.

## 7. Despliegue

Render usa el contexto completo del repositorio porque el backend depende de la
librería situada en `engine/`. El `render.yaml` ya no usa el campo no necesario
`dockerContext`.
