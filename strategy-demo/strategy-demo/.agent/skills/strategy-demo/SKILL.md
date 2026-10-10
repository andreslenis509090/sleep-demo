---
name: strategy-demo
description: Úsala cuando se pida construir o modificar la API FastAPI, la página HTML o las pruebas de la demo del patrón Strategy (RN03, días críticos) del proyecto de higiene del sueño. Contiene el contrato de endpoints, el comportamiento del frontend y los resultados esperados para verificar.
---

# Demo web del patrón Strategy

## Principio
La API y el frontend solo exponen el patrón. Toda decisión sobre qué es un día crítico la toma una estrategia de `patron_strategy.py` (`CriterioMetaPersonal`, `CriterioUmbralPorDefecto`, `CriterioMetaConTolerancia`) a través de `MetricaSemanal`. No reimplementar esa lógica en `app.py` ni en el JavaScript.

## Endpoints
### GET /api/estrategias
Devuelve la lista `[{id, nombre}]` de las estrategias que el cliente puede pedir:
`meta_personal`, `umbral_por_defecto`, `meta_con_tolerancia`.

### POST /api/metricas/semanal
Entrada (JSON):
- `usuario`: `{nombre: str, meta_sueno: float | null}` (0 < meta <= 24)
- `semana_inicio`: fecha ISO
- `registros`: lista de `{fecha, hora_acostarse "HH:MM", hora_despertar "HH:MM", calificacion 1-5}`
- `estrategia`: id opcional; si es `null`, se elige por RN03 (`elegir_criterio`)
- `tolerancia_horas`: float, solo se usa con `meta_con_tolerancia` (por defecto 0.5)

Salida (JSON): `estrategia` (nombre), `umbral`, `dias` (`[{fecha, horas, critico}]`), `promedio_semanal`, `dias_criticos`.

Errores:
- 404 si el id de estrategia no existe.
- 422 con el mensaje del `ValueError` si se pide `meta_personal` y el usuario no tiene meta.

Usar modelos Pydantic para entrada y salida. Para crear `MetricaSemanal` pasar `criterio=None` cuando no se pidió estrategia.

## Frontend (index.html)
Una sola página, JS plano con `fetch`, servida por FastAPI en `/`:
- Campos: nombre, meta de sueño (vacía = sin meta), selector de criterio (primera opción "Automático (RN03)"; el resto se carga desde `/api/estrategias`), tolerancia.
- Tabla de 7 días con hora de acostarse y de despertar editables, precargada con la semana de ejemplo.
- Botón "Calcular métricas" que llama a la API.
- Resultado: línea con estrategia, umbral y promedio; **gráfica de barras** de horas por día (HU2), **barra roja** en los días críticos, línea punteada en el umbral.
- Si la API responde error, mostrar el mensaje en la página (no solo en consola).

## Semana de ejemplo (lunes 2026-10-05)
| Día | Acostarse | Despertar | Calificación | Horas |
|---|---|---|---|---|
| Lun 05 | 22:30 | 06:30 | 4 | 8.0 |
| Mar 06 | 23:30 | 05:30 | 2 | 6.0 |
| Mié 07 | 00:30 | 06:00 | 2 | 5.5 |
| Jue 08 | 23:00 | 06:45 | 4 | 7.75 |
| Vie 09 | 01:00 | 06:30 | 1 | 5.5 |
| Sáb 10 | 22:00 | 06:30 | 5 | 8.5 |
| Dom 11 | 23:00 | 06:30 | 3 | 7.5 |

## Resultados esperados (para verificar cada paso)
Promedio semanal en todos los casos: **7.0 h**.

| Caso | Estrategia usada | Umbral | Días críticos |
|---|---|---|---|
| Meta 8 h, estrategia automática | Meta personal | 8.0 | 06, 07, 08, 09 y 11 de oct |
| Sin meta, estrategia automática | Umbral por defecto (6 h) | 6.0 | 07 y 09 de oct |
| Meta 8 h, `umbral_por_defecto` | Umbral por defecto (6 h) | 6.0 | 07 y 09 de oct |
| Meta 8 h, `meta_con_tolerancia` (0.5) | Meta con tolerancia (0.5 h) | 7.5 | 06, 07 y 09 de oct |
| Sin meta, `meta_personal` | (error 422) | — | "El usuario no definió meta de sueño" |
| Estrategia `nope` | (error 404) | — | "Estrategia desconocida: nope" |

## Cómo ejecutar
```
pip install -r requirements.txt
uvicorn app:app --reload
```
Abrir http://127.0.0.1:8000 (página) y http://127.0.0.1:8000/docs (Swagger).

## Pruebas (opcional, paso final)
Con `pytest` y `fastapi.testclient`, una prueba por fila de la tabla de resultados esperados.
