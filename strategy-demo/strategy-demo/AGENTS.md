# strategy-demo

Demo de la entrega "Implementación patrón de diseño de software" (ITM).
Patrón: **Strategy** (comportamiento). Proyecto: Sistema de Monitoreo de Higiene del Sueño.

## Qué es esto
- `patron_strategy.py` es el **núcleo del patrón** y ya está terminado y probado. No se modifica salvo que yo lo pida explícitamente.
- Lo que se construye ahora es solo una capa para **mostrar** el patrón: una API en FastAPI y una página HTML básica.

## Regla de negocio que implementa el patrón
RN03: un día es crítico cuando las horas dormidas son inferiores a la meta personal del usuario; si no definió meta, el umbral por defecto es 6 horas.

## Reglas de trabajo
- Stack: Python 3.10+, FastAPI, uvicorn. Sin base de datos, sin autenticación, sin librerías extra de frontend (HTML + CSS + JS plano).
- `app.py` NO contiene lógica del patrón: solo recibe la petición, arma los objetos del dominio, elige la estrategia y devuelve el resultado. Ningún `if` que decida si un día es crítico.
- Nombres de clases y atributos sin tilde ni eñe (`MetricaSemanal`, `RegistroSueno`, `meta_sueno`).
- Trabajar **un paso a la vez**. Al terminar cada paso: ejecutar lo que corresponda, mostrarme la salida real y detenerte. No avances al siguiente paso sin mi confirmación.
- Si algo del código existente parece un error, avísame antes de cambiarlo.

## Estructura esperada
```
strategy-demo/
├── AGENTS.md
├── .agent/skills/strategy-demo/SKILL.md
├── patron_strategy.py
├── app.py
├── index.html
└── requirements.txt
```
