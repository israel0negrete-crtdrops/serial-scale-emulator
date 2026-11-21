"""Comportamiento: qué peso hay y cómo se porta la báscula. No sabe de puertos.

Modo normal: un peso sintético (fijo, o que fluctúa alrededor de un valor),
siempre con la misma semilla para que una corrida se pueda repetir.

Modo de fallas: cada solicitud toma la siguiente acción de un guion, o una al
azar con probabilidades. Las acciones:

    normal            contesta el peso
    tardia:MS         contesta, pero MS milisegundos después
    sin_respuesta     no contesta
    incompleta        manda media trama, sin terminador
    invalida          manda una trama con el formato roto
    desconexion:S     cierra el puerto S segundos (en el gadget USB el enlace
                      sigue arriba: la computadora ve silencio, no un
                      desconectado; para eso hay que desconectar el cable)

Un guion se escribe así: "normal*3,tardia:800,sin_respuesta,normal*2".
Al acabarse, sigue en normal.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from protocolo import PESO_MAXIMO, TERMINADOR, respuesta

ACCIONES = ("normal", "tardia", "sin_respuesta", "incompleta", "invalida", "desconexion")


@dataclass
class Plan:
    """Lo que el emulador debe hacer con una solicitud."""
    accion: str
    trama: bytes | None          # None: no mandar nada
    retraso_ms: int = 0
    desconectar_s: float = 0.0
    peso: float | None = None


def leer_guion(texto: str) -> list[tuple[str, float]]:
    pasos: list[tuple[str, float]] = []
    for parte in (p.strip() for p in texto.split(",") if p.strip()):
        veces = 1
        if "*" in parte:
            parte, n = parte.split("*")
            veces = int(n)
        nombre, _, valor = parte.partition(":")
        if nombre not in ACCIONES:
            raise ValueError(f"acción desconocida: {nombre}")
        pasos += [(nombre, float(valor) if valor else 0.0)] * veces
    return pasos


class Bascula:
    def __init__(self, peso: float = 12.5, fluctuacion: float = 0.0, semilla: int = 1,
                 guion: str = "", probabilidades: dict[str, float] | None = None,
                 retraso_tardio_ms: int = 800, desconexion_s: float = 5.0):
        if not 0 <= peso <= PESO_MAXIMO:
            raise ValueError("peso fuera de rango")
        self.base, self.fluctuacion = peso, fluctuacion
        self.rng = random.Random(semilla)
        self.guion = leer_guion(guion)
        self.probabilidades = probabilidades or {}
        self.retraso_tardio_ms, self.desconexion_s = retraso_tardio_ms, desconexion_s
        self.solicitudes = 0

    def peso(self) -> float:
        """El peso de ahora: el base, o el base más una fluctuación al azar."""
        p = self.base + (self.rng.uniform(-self.fluctuacion, self.fluctuacion) if self.fluctuacion else 0)
        return round(min(max(p, 0.0), PESO_MAXIMO), 1)

    def _accion(self) -> tuple[str, float]:
        if self.solicitudes < len(self.guion):
            return self.guion[self.solicitudes]
        r, acumulado = self.rng.random(), 0.0
        for nombre, prob in self.probabilidades.items():
            acumulado += prob
            if r < acumulado:
                return nombre, 0.0
        return "normal", 0.0

    def atender(self) -> Plan:
        """Decide qué hacer con una solicitud de peso."""
        nombre, valor = self._accion()
        self.solicitudes += 1
        peso = self.peso()
        buena = respuesta(peso)
        if nombre == "normal":
            return Plan(nombre, buena, peso=peso)
        if nombre == "tardia":
            return Plan(nombre, buena, retraso_ms=int(valor or self.retraso_tardio_ms), peso=peso)
        if nombre == "sin_respuesta":
            return Plan(nombre, None)
        if nombre == "incompleta":
            return Plan(nombre, buena[:3])                       # "+12", sin el resto ni el terminador
        if nombre == "invalida":
            return Plan(nombre, b"+1?.5" + TERMINADOR)
        return Plan(nombre, None, desconectar_s=valor or self.desconexion_s)
