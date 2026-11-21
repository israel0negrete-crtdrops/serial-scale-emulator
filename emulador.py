#!/usr/bin/env python3
"""La báscula: escucha en un puerto serial y contesta como una báscula.

    python3 emulador.py --puerto /dev/ttyGS0                       # modo normal
    python3 emulador.py --puerto /dev/ttyGS0 --fluctuacion 0.3
    python3 emulador.py --puerto /dev/ttyGS0 --guion "normal*5,tardia:800,sin_respuesta,incompleta,invalida"
    python3 emulador.py --puerto /dev/ttyGS0 --periodico 5         # además, el peso cada 5 s (pruebas)

Junta las tres capas: transporte (el puerto), protocolo (la `P` y la trama) y
comportamiento (el peso y las fallas). Con --registro anota cada solicitud:
cuándo llegó el comando y cuándo terminó de salir la respuesta, medido aquí,
del lado del emulador. Lo que tarda en llegar a la aplicación, con el USB y su
lectura, se mide aparte, desde la computadora (cliente.py): no se mezclan.
"""
from __future__ import annotations

import argparse
import csv
import signal
import sys
import time

from comportamiento import Bascula
from protocolo import comandos, respuesta
from transporte import Puerto, ahora_ns


class Emulador:
    def __init__(self, ruta: str, bascula: Bascula, periodico_s: float = 0.0, registro: str | None = None):
        self.ruta, self.bascula, self.periodico_s = ruta, bascula, periodico_s
        self.puerto = Puerto(ruta)
        self.seguir = True
        self._archivo = open(registro, "w", newline="") if registro else None
        self._csv = csv.writer(self._archivo) if self._archivo else None
        if self._csv:
            self._csv.writerow(["n", "accion", "peso", "bytes", "retraso_ms", "t_comando_ns", "t_enviado_ns", "us_respuesta"])

    def _anotar(self, n, plan, t0, t1):
        if self._csv:
            us = (t1 - t0) // 1000 if t1 else ""
            self._csv.writerow([n, plan.accion, plan.peso if plan.peso is not None else "",
                                len(plan.trama or b""), plan.retraso_ms, t0, t1 or "", us])
            self._archivo.flush()

    def atender(self, t_comando: int) -> None:
        plan = self.bascula.atender()
        n = self.bascula.solicitudes
        if plan.desconectar_s:
            self.puerto.cerrar()
            time.sleep(plan.desconectar_s)
            self.puerto = Puerto(self.ruta)
            self._anotar(n, plan, t_comando, None)
            return
        if plan.retraso_ms:
            time.sleep(plan.retraso_ms / 1000)
        t_enviado = None
        if plan.trama is not None:
            self.puerto.escribir(plan.trama)
            t_enviado = ahora_ns()
        self._anotar(n, plan, t_comando, t_enviado)

    def _enlace(self, estado: str) -> None:
        """Anota en el log (stderr) cuándo se cae o vuelve el enlace, con el reloj de aquí."""
        print(f"enlace {estado} t_reloj={time.time():.3f} t_mono_ns={ahora_ns()}", file=sys.stderr, flush=True)

    def correr(self) -> None:
        proximo = time.monotonic() + self.periodico_s if self.periodico_s else None
        caido = False
        while self.seguir:
            espera = 0.2 if proximo is None else max(0.0, min(0.2, proximo - time.monotonic()))
            try:
                datos = self.puerto.leer(espera)
                if caido:
                    # Sólo dice que el puerto se pudo reabrir: desde aquí no se
                    # sabe si el anfitrión ya volvió (eso lo ve la computadora).
                    caido = False
                    self._enlace("reabierto")
                t = ahora_ns()
                for _ in range(comandos(datos)):
                    self.atender(t)
                if proximo is not None and time.monotonic() >= proximo:
                    # Envío periódico, sólo para pruebas: no todos los modelos lo hacen.
                    self.puerto.escribir(respuesta(self.bascula.peso()))
                    proximo += self.periodico_s
            except (ConnectionError, OSError) as e:
                # En el gadget, si el anfitrión se va, Linux puede colgarle el
                # puerto: una báscula de verdad sigue prendida, así que se
                # reabre y se espera a que el enlace vuelva.
                if not caido:
                    caido = True
                    self._enlace(f"caido ({e.__class__.__name__}: {e})")
                self.puerto.cerrar()
                time.sleep(0.2)
                try:
                    self.puerto = Puerto(self.ruta)
                except OSError:
                    pass
        self.puerto.cerrar()
        if self._archivo:
            self._archivo.close()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--puerto", default="/dev/ttyGS0")
    ap.add_argument("--peso", type=float, default=12.5)
    ap.add_argument("--fluctuacion", type=float, default=0.0, help="± kg alrededor del peso")
    ap.add_argument("--semilla", type=int, default=1)
    ap.add_argument("--guion", default="", help='p. ej. "normal*3,tardia:800,sin_respuesta"')
    ap.add_argument("--azar", default="", help='fallas al azar, p. ej. "tardia=0.1,sin_respuesta=0.05"')
    ap.add_argument("--periodico", type=float, default=0.0, help="manda el peso cada N s, además de contestar")
    ap.add_argument("--registro", help="CSV con una fila por solicitud")
    a = ap.parse_args()
    prob = {k: float(v) for k, v in (x.split("=") for x in a.azar.split(",") if x)}
    emu = Emulador(a.puerto, Bascula(a.peso, a.fluctuacion, a.semilla, a.guion, prob), a.periodico, a.registro)

    def parar(*_):
        emu.seguir = False

    signal.signal(signal.SIGTERM, parar)
    signal.signal(signal.SIGINT, parar)
    print(f"báscula escuchando en {a.puerto}", file=sys.stderr, flush=True)
    emu.correr()


if __name__ == "__main__":
    main()
