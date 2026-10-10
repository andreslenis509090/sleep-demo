"""
Patrón Strategy aplicado a RN03 - Sistema de Monitoreo de Higiene del Sueño.

RN03: un día es crítico cuando las horas dormidas son inferiores a la meta
personal del usuario; si no definió meta, se usa un umbral por defecto de 6 h.
Cada forma de decidir "qué es un día crítico" es una estrategia intercambiable.

Ejecución: python patron_strategy.py   (no requiere librerías externas)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import List, Optional

UMBRAL_POR_DEFECTO = 6.0  # horas (RN03)


# ---------------------------------------------------------------- dominio
@dataclass
class Usuario:
    nombre: str
    meta_sueno: Optional[float] = None  # horas; None si no la definió (RF01)


@dataclass
class RegistroSueno:
    fecha: date
    hora_acostarse: time
    hora_despertar: time
    calificacion: int  # 1-5

    def calcular_duracion(self) -> float:
        """Horas dormidas; soporta que el sueño cruce la medianoche (RF04)."""
        inicio = datetime.combine(self.fecha, self.hora_acostarse)
        fin = datetime.combine(self.fecha, self.hora_despertar)
        if fin <= inicio:
            fin += timedelta(days=1)
        return round((fin - inicio).total_seconds() / 3600, 2)


# ---------------------------------------------------------------- Strategy
class CriterioDiaCritico(ABC):
    """Interfaz Strategy: define CÓMO se decide si un día es crítico."""

    nombre: str = "criterio"

    @abstractmethod
    def umbral(self, usuario: Usuario) -> float:
        """Horas mínimas por debajo de las cuales el día es crítico."""

    def es_critico(self, horas_dormidas: float, usuario: Usuario) -> bool:
        """Comportamiento común; una estrategia puede sobrescribirlo."""
        return horas_dormidas < self.umbral(usuario)


class CriterioMetaPersonal(CriterioDiaCritico):
    """Estrategia concreta 1: compara contra la meta del perfil del usuario."""

    nombre = "Meta personal"

    def umbral(self, usuario: Usuario) -> float:
        if usuario.meta_sueno is None:
            raise ValueError("El usuario no definió meta de sueño")
        return usuario.meta_sueno


class CriterioUmbralPorDefecto(CriterioDiaCritico):
    """Estrategia concreta 2: compara contra el umbral fijo de 6 horas."""

    nombre = "Umbral por defecto (6 h)"

    def umbral(self, usuario: Usuario) -> float:
        return UMBRAL_POR_DEFECTO


class CriterioMetaConTolerancia(CriterioDiaCritico):
    """Estrategia concreta 3 (SOLO DEMOSTRACIÓN, no hace parte de RN03).

    Meta personal menos un margen de tolerancia. Se agrega únicamente para
    mostrar que un criterio nuevo no obliga a modificar MetricaSemanal ni las
    estrategias existentes.
    """

    def __init__(self, tolerancia_horas: float = 0.5):
        self.tolerancia_horas = tolerancia_horas
        self.nombre = f"Meta con tolerancia ({tolerancia_horas} h)"

    def umbral(self, usuario: Usuario) -> float:
        if usuario.meta_sueno is None:
            raise ValueError("El usuario no definió meta de sueño")
        return usuario.meta_sueno - self.tolerancia_horas


def elegir_criterio(usuario: Usuario) -> CriterioDiaCritico:
    """Aplica RN03: meta personal si existe, si no el umbral por defecto."""
    if usuario.meta_sueno is not None:
        return CriterioMetaPersonal()
    return CriterioUmbralPorDefecto()


# ---------------------------------------------------------------- Context
class MetricaSemanal:
    """Contexto: usa un CriterioDiaCritico sin conocer su implementación."""

    def __init__(self, usuario: Usuario, semana_inicio: date,
                 registros: List[RegistroSueno],
                 criterio: Optional[CriterioDiaCritico] = None):
        self.usuario = usuario
        self.semana_inicio = semana_inicio
        self.semana_fin = semana_inicio + timedelta(days=6)
        self.registros = registros
        # Si no se inyecta un criterio, se elige según RN03.
        self._criterio = criterio or elegir_criterio(usuario)

    def set_criterio(self, criterio: CriterioDiaCritico) -> None:
        """Permite cambiar el algoritmo en tiempo de ejecución."""
        self._criterio = criterio

    @property
    def criterio(self) -> CriterioDiaCritico:
        return self._criterio

    def calcular_promedio(self) -> float:
        """Promedio semanal con un decimal (RF11, HU2)."""
        if not self.registros:
            return 0.0
        total = sum(r.calcular_duracion() for r in self.registros)
        return round(total / len(self.registros), 1)

    def marcar_dias_criticos(self) -> List[date]:
        """Delegación: la decisión la toma la estrategia (RF12)."""
        return [
            r.fecha for r in self.registros
            if self._criterio.es_critico(r.calcular_duracion(), self.usuario)
        ]


# ---------------------------------------------------------------- demo
def _semana(inicio: date) -> List[RegistroSueno]:
    """Semana de ejemplo: (hora de acostarse, hora de despertar, calificación)."""
    datos = [
        (time(22, 30), time(6, 30), 4),  # 8.0 h
        (time(23, 30), time(5, 30), 2),  # 6.0 h
        (time(0, 30), time(6, 0), 2),    # 5.5 h
        (time(23, 0), time(6, 45), 4),   # 7.75 h
        (time(1, 0), time(6, 30), 1),    # 5.5 h
        (time(22, 0), time(6, 30), 5),   # 8.5 h
        (time(23, 0), time(6, 30), 3),   # 7.5 h
    ]
    return [RegistroSueno(inicio + timedelta(days=i), a, d, c)
            for i, (a, d, c) in enumerate(datos)]


def _imprimir(metrica: MetricaSemanal) -> None:
    u = metrica.usuario
    meta = f"{u.meta_sueno} h" if u.meta_sueno is not None else "sin meta"
    print(f"\nUsuario: {u.nombre} ({meta})")
    print(f"Estrategia: {metrica.criterio.nombre} -> "
          f"umbral {metrica.criterio.umbral(u)} h")
    for r in metrica.registros:
        h = r.calcular_duracion()
        marca = " <-- CRÍTICO" if metrica.criterio.es_critico(h, u) else ""
        print(f"  {r.fecha:%a %d-%b}: {h:>5.2f} h{marca}")
    print(f"Promedio semanal: {metrica.calcular_promedio()} h")
    print("Días críticos:",
          [f"{d:%d-%b}" for d in metrica.marcar_dias_criticos()])


if __name__ == "__main__":
    lunes = date(2026, 10, 5)
    registros = _semana(lunes)

    print("=" * 60)
    print("1) Misma semana, dos usuarios -> la estrategia se elige por RN03")
    print("=" * 60)
    _imprimir(MetricaSemanal(Usuario("Ana", meta_sueno=8.0), lunes, registros))
    _imprimir(MetricaSemanal(Usuario("Luis"), lunes, registros))

    print("\n" + "=" * 60)
    print("2) Cambio de estrategia en tiempo de ejecución (Ana)")
    print("=" * 60)
    ana = Usuario("Ana", meta_sueno=8.0)
    metrica = MetricaSemanal(ana, lunes, registros)
    _imprimir(metrica)
    metrica.set_criterio(CriterioUmbralPorDefecto())
    print("\n>> set_criterio(CriterioUmbralPorDefecto())")
    _imprimir(metrica)

    print("\n" + "=" * 60)
    print("3) Nueva estrategia sin modificar MetricaSemanal (extensibilidad)")
    print("=" * 60)
    metrica.set_criterio(CriterioMetaConTolerancia(0.5))
    print("\n>> set_criterio(CriterioMetaConTolerancia(0.5))")
    _imprimir(metrica)
