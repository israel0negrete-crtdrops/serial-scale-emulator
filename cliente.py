#!/usr/bin/env python3
"""Lo que hace la aplicación: pide el peso y mide, desde la computadora.

    python3 cliente.py --puerto /dev/tty.usbmodem1101 --veces 200 --cada 0.25 --registro c.csv

Por cada consulta: descarta lo pendiente, manda `P`, lee hasta el terminador
con un tiempo límite y clasifica lo que pasó:

    ok            trama completa y válida
    sin_respuesta no llegó nada antes del límite
    incompleta    llegaron bytes, pero no el terminador
    invalida      trama completa con el formato roto
    desconectado  el puerto desapareció; reintenta abrirlo cada medio segundo

El tiempo medido va de antes de mandar la `P` a que llega el terminador: el
recorrido completo que vive la aplicación, USB incluido. No es el tiempo del
emulador (ése lo anota emulador.py del otro lado).
"""
from __future__ import annotations

import argparse
import csv
import signal
import statistics
import time

from protocolo import PEDIR_PESO, TERMINADOR, leer_respuesta
from transporte import Puerto, ahora_ns


def consultar(puerto: Puerto, limite_s: float) -> tuple[str, float | None, int, bytes]:
    """Una consulta. Devuelve (resultado, peso, microsegundos, bytes recibidos)."""
    puerto.descartar()
    t0 = ahora_ns()
    puerto.escribir(PEDIR_PESO, drenar=False)
    recibido = b""
    fin = time.monotonic() + limite_s
    while TERMINADOR not in recibido:
        resta = fin - time.monotonic()
        if resta <= 0:
            return ("incompleta" if recibido else "sin_respuesta"), None, (ahora_ns() - t0) // 1000, recibido
        recibido += puerto.leer(resta)
    us = (ahora_ns() - t0) // 1000
    trama = recibido[: recibido.index(TERMINADOR) + len(TERMINADOR)]
    try:
        return "ok", leer_respuesta(trama), us, recibido
    except ValueError:
        return "invalida", None, us, recibido


def reabrir(ruta: str, hasta_s: float) -> Puerto | None:
    fin = time.monotonic() + hasta_s
    while time.monotonic() < fin:
        try:
            return Puerto(ruta)
        except OSError:
            time.sleep(0.5)
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--puerto", required=True)
    ap.add_argument("--veces", type=int, default=100)
    ap.add_argument("--cada", type=float, default=0.25, help="segundos entre consultas")
    ap.add_argument("--limite", type=float, default=1.0, help="segundos de espera por respuesta")
    ap.add_argument("--reconectar", type=float, default=30.0, help="segundos intentando reabrir")
    ap.add_argument("--registro")
    a = ap.parse_args()

    def interrumpir(*_):
        raise KeyboardInterrupt

    # Detenerlo antes de tiempo (SIGTERM o Ctrl+C) guarda lo medido hasta ahí.
    signal.signal(signal.SIGTERM, interrumpir)
    puerto: Puerto | None = Puerto(a.puerto)
    filas = []
    try:
        for n in range(1, a.veces + 1):
            t_inicio = time.time()
            try:
                if puerto is None:
                    raise OSError("sin puerto")
                res, peso, us, crudo = consultar(puerto, a.limite)
            except (OSError, ConnectionError):
                if puerto:
                    puerto.cerrar()
                t_perdido = time.monotonic()
                puerto = reabrir(a.puerto, a.reconectar)
                res, peso, us, crudo = "desconectado", None, int((time.monotonic() - t_perdido) * 1e6), b""
            filas.append({"n": n, "t": round(t_inicio, 3), "resultado": res, "peso": peso, "us": us, "crudo": crudo.decode("ascii", "replace")})
            print(f"{n:4d} {res:13s} {'' if peso is None else peso:>6} {us/1000:9.2f} ms {crudo!r}", flush=True)
            time.sleep(a.cada)
    except KeyboardInterrupt:
        print("detenido: se guarda lo medido", flush=True)
    if puerto:
        puerto.cerrar()

    if a.registro:
        with open(a.registro, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(filas[0]))
            w.writeheader()
            w.writerows(filas)
    ok = [x["us"] / 1000 for x in filas if x["resultado"] == "ok"]
    cuenta = {r: sum(1 for x in filas if x["resultado"] == r) for r in {x["resultado"] for x in filas}}
    print("resultados", cuenta)
    if len(ok) >= 2:
        ok.sort()
        print(f"ok: mediana {statistics.median(ok):.2f} ms · p95 {ok[int(0.95 * (len(ok) - 1))]:.2f} ms · máx {ok[-1]:.2f} ms")


if __name__ == "__main__":
    main()
