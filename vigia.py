#!/usr/bin/env python3
"""Anota cuándo cambia el enlace USB, visto desde un lado. No sabe de básculas.

    python3 vigia.py --estado /sys/class/udc/3f980000.usb/state --registro p.csv   # en la Pi
    python3 vigia.py --existe /dev/cu.usbmodem1301 --registro m.csv               # en la Mac

Revisa cada 10 ms y escribe una fila por cambio (hora del reloj de ese equipo y
monotónica). Cada lado tiene su propio reloj: los registros no se mezclan.
"""
from __future__ import annotations

import argparse
import os
import signal
import time


def leer(a) -> str:
    if a.existe:
        return "presente" if os.path.exists(a.existe) else "ausente"
    try:
        return open(a.estado).read().strip()
    except OSError:
        return "sin_estado"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--estado", help="archivo cuyo contenido es el estado (p. ej. el del UDC)")
    g.add_argument("--existe", help="ruta cuya presencia es el estado (p. ej. el puerto)")
    ap.add_argument("--registro", required=True)
    ap.add_argument("--cada", type=float, default=0.01)
    a = ap.parse_args()
    seguir = True

    def parar(*_):
        nonlocal seguir
        seguir = False

    signal.signal(signal.SIGTERM, parar)
    signal.signal(signal.SIGINT, parar)
    anterior = None
    with open(a.registro, "w") as f:
        f.write("t_reloj,t_mono_ns,estado\n")
        while seguir:
            e = leer(a)
            if e != anterior:
                f.write(f"{time.time():.3f},{time.monotonic_ns()},{e}\n")
                f.flush()
                anterior = e
            time.sleep(a.cada)


if __name__ == "__main__":
    main()
