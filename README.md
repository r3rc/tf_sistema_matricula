# Sistema de Matrícula – Colegio Peruano de Ciencias

Trabajo final del curso **Fundamentos de Programación**.

- **Ciclo:** 2026-2
- **Profesor:** ROJAS RAMOS, CHRISTIAN GENARO

## Integrantes

- BUENO HUAMANYAURI, ALVARO JAVIER
- ROMAN YAURIS, JHYRALD FIPPOS
- ROSAS ROSALES, RENZO ALEJANDRO
- VEGA HUAYNATE, DIEGO ALONSO

## Descripción

Aplicación de consola en Python que apoya a la secretaría del colegio en el proceso de matrícula: registro de solicitudes, control de documentos, validación según las vacantes disponibles, registro de pago, constancia de vacante y matrícula final tras la liberación en SIAGIE.

Los datos se guardan en archivos CSV, por lo que no requiere instalar librerías externas.

## Requisitos

- Python 3.8 o superior (solo se usa la biblioteca estándar: `os`, `csv`, `datetime`).

## Ejecución

```bash
python3 matricula.py
```

Ejecútalo desde la carpeta del proyecto, ya que lee y escribe en `datos/`.

## Archivos de datos

**`datos/vacantes.csv`**

```csv
grado,cupos_totales,cupos_disponibles
Inicial 5 anios,18,8
1ro de primaria,16,8
1ro de secundaria,14,8
```

**`datos/solicitudes.csv`** — columnas: `dni`, `nombre`, `apellido`, `fecha_nacimiento`, `grado`, `colegio_procedencia`, `doc_dni`, `doc_partida_nacimiento`, `doc_comprobante_pago`, `estado`.

Los registros incluidos son **datos ficticios de prueba** (43 solicitudes en distintos estados) para demostrar el flujo completo.
