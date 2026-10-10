from __future__ import annotations

import os
from datetime import date, time
from typing import List, Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from patron_strategy import (
    CriterioMetaPersonal,
    CriterioUmbralPorDefecto,
    CriterioMetaConTolerancia,
    MetricaSemanal,
    RegistroSueno,
    Usuario,
)

app = FastAPI(title="Demo Patrón Strategy - Higiene del Sueño")


# ---------------------------------------------------------------- Modelos Pydantic
class EstrategiaItem(BaseModel):
    id: str
    nombre: str


class UsuarioInput(BaseModel):
    nombre: str
    meta_sueno: Optional[float] = Field(default=None, gt=0, le=24)


class RegistroInput(BaseModel):
    fecha: date
    hora_acostarse: time
    hora_despertar: time
    calificacion: int = Field(ge=1, le=5)


class MetricasRequest(BaseModel):
    usuario: UsuarioInput
    semana_inicio: date
    registros: List[RegistroInput]
    estrategia: Optional[str] = None
    tolerancia_horas: float = 0.5


class DiaResultado(BaseModel):
    fecha: date
    horas: float
    critico: bool


class MetricasResponse(BaseModel):
    estrategia: str
    umbral: float
    dias: List[DiaResultado]
    promedio_semanal: float
    dias_criticos: List[date]


# ---------------------------------------------------------------- Endpoints
@app.get("/")
def root():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"message": "API de demostración de Patrón Strategy"}


@app.get("/api/estrategias", response_model=List[EstrategiaItem])
def listar_estrategias():
    return [
        EstrategiaItem(id="meta_personal", nombre="Meta personal"),
        EstrategiaItem(id="umbral_por_defecto", nombre="Umbral por defecto (6 h)"),
        EstrategiaItem(id="meta_con_tolerancia", nombre="Meta con tolerancia"),
    ]


@app.post("/api/metricas/semanal", response_model=MetricasResponse)
def calcular_metricas_semanal(req: MetricasRequest):
    # Selección de estrategia si fue solicitada explícitamente
    criterio = None
    if req.estrategia is not None:
        if req.estrategia == "meta_personal":
            criterio = CriterioMetaPersonal()
        elif req.estrategia == "umbral_por_defecto":
            criterio = CriterioUmbralPorDefecto()
        elif req.estrategia == "meta_con_tolerancia":
            criterio = CriterioMetaConTolerancia(tolerancia_horas=req.tolerancia_horas)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Estrategia desconocida: {req.estrategia}",
            )

    # Armar los objetos de dominio
    usuario_dominio = Usuario(
        nombre=req.usuario.nombre,
        meta_sueno=req.usuario.meta_sueno,
    )
    registros_dominio = [
        RegistroSueno(
            fecha=r.fecha,
            hora_acostarse=r.hora_acostarse,
            hora_despertar=r.hora_despertar,
            calificacion=r.calificacion,
        )
        for r in req.registros
    ]

    # Delegación completa en MetricaSemanal y el Criterio
    try:
        metrica = MetricaSemanal(
            usuario=usuario_dominio,
            semana_inicio=req.semana_inicio,
            registros=registros_dominio,
            criterio=criterio,
        )
        umbral_calculado = metrica.criterio.umbral(metrica.usuario)
        dias_criticos_fechas = metrica.marcar_dias_criticos()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    conjunto_criticos = set(dias_criticos_fechas)
    dias_resultado = [
        DiaResultado(
            fecha=r.fecha,
            horas=r.calcular_duracion(),
            critico=(r.fecha in conjunto_criticos),
        )
        for r in metrica.registros
    ]

    return MetricasResponse(
        estrategia=metrica.criterio.nombre,
        umbral=umbral_calculado,
        dias=dias_resultado,
        promedio_semanal=metrica.calcular_promedio(),
        dias_criticos=dias_criticos_fechas,
    )
