"""Protocolo: qué se pide y qué se contesta. No sabe de puertos ni de fallas.

Es un protocolo DIDÁCTICO, inspirado en el de una báscula comercial pero sin
pretender reproducirlo entero:

- La aplicación manda el carácter ASCII `P` para pedir el peso (eso sí viene
  del protocolo original).
- La báscula contesta el peso en ASCII con signo y un decimal: `+12.5`.
- Termina con CR LF. **Supuesto nuestro:** del protocolo original no está
  confirmado el terminador ni si había más campos.

Todo lo que no sea `P` se ignora, como haría un equipo que sólo entiende un
comando.
"""
from __future__ import annotations

import re

PEDIR_PESO = b"P"
TERMINADOR = b"\r\n"
_FORMATO = re.compile(rb"^[+-]\d{2}\.\d$")
PESO_MAXIMO = 99.9


def respuesta(peso: float) -> bytes:
    """El peso como lo manda la báscula: `+05.2\\r\\n`."""
    if not 0 <= peso <= PESO_MAXIMO:
        raise ValueError(f"fuera de rango: {peso}")
    return f"+{peso:04.1f}".encode("ascii") + TERMINADOR


def comandos(datos: bytes) -> int:
    """Cuántas solicitudes de peso trae lo que llegó."""
    return datos.count(PEDIR_PESO)


def leer_respuesta(trama: bytes) -> float:
    """Lo que debería hacer la aplicación al recibir una trama completa.

    Devuelve el peso o lanza ValueError si la trama no tiene el formato.
    """
    if not trama.endswith(TERMINADOR):
        raise ValueError(f"trama sin terminador: {trama!r}")
    cuerpo = trama[: -len(TERMINADOR)]
    if not _FORMATO.match(cuerpo):
        raise ValueError(f"formato inválido: {cuerpo!r}")
    return float(cuerpo)
