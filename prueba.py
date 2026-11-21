#!/usr/bin/env python3
"""Pruebas sin hardware: el emulador en un lado de un pseudoterminal y la
aplicación (cliente.consultar) en el otro.

    python3 prueba.py

Comprueban el formato de la trama, la lógica de consulta, cada falla del modo
de fallas, el envío periódico y que el registro del emulador mida lo suyo.
"""
from __future__ import annotations

import csv
import os
import sys
import tempfile
import threading
import time

from cliente import consultar
from comportamiento import Bascula, leer_guion
from emulador import Emulador
from protocolo import leer_respuesta, respuesta
from transporte import Puerto

fallas = 0


def ok(nombre, cond, detalle=""):
    global fallas
    print(f"  {'ok ' if cond else 'MAL'} {nombre}{'' if cond else '  ' + str(detalle)}")
    fallas += not cond


class Banco:
    """Un emulador corriendo en un hilo, sobre la mitad esclava de un pty."""

    def __init__(self, bascula, periodico_s=0.0):
        self.maestro, esclavo = os.openpty()
        self.ruta = os.ttyname(esclavo)
        self.registro = tempfile.mktemp(suffix=".csv")
        self.emu = Emulador(self.ruta, bascula, periodico_s, self.registro)
        os.close(esclavo)            # el emulador abrió la suya
        self.app = Puerto(fd=self.maestro)
        self.hilo = threading.Thread(target=self.emu.correr, daemon=True)
        self.hilo.start()

    def consultar(self, limite=0.5):
        try:
            return consultar(self.app, limite)
        except (OSError, ConnectionError):
            return "desconectado", None, 0, b""

    def cerrar(self):
        self.emu.seguir = False
        self.hilo.join(timeout=3)
        self.app.cerrar()
        filas = list(csv.DictReader(open(self.registro)))
        os.unlink(self.registro)
        return filas


def main() -> None:
    print("protocolo")
    ok("la trama del peso", respuesta(5.2) == b"+05.2\r\n" and respuesta(12.5) == b"+12.5\r\n")
    ok("ida y vuelta", leer_respuesta(respuesta(37.4)) == 37.4)
    for mala in (b"+1?.5\r\n", b"12.5\r\n", b"+12.5", b"+125.0\r\n"):
        try:
            leer_respuesta(mala)
            ok(f"rechaza {mala!r}", False)
        except ValueError:
            ok(f"rechaza {mala!r}", True)
    try:
        respuesta(100.0)
        ok("no hay peso de tres cifras", False)
    except ValueError:
        ok("no hay peso de tres cifras", True)

    print("comportamiento")
    ok("el guion se expande", leer_guion("normal*2,tardia:300,sin_respuesta") ==
       [("normal", 0.0), ("normal", 0.0), ("tardia", 300.0), ("sin_respuesta", 0.0)])
    a, b = Bascula(20, 0.5, semilla=7), Bascula(20, 0.5, semilla=7)
    pa, pb = [a.peso() for _ in range(50)], [b.peso() for _ in range(50)]
    ok("misma semilla, mismos pesos", pa == pb)
    ok("la fluctuación no se sale del rango", all(19.5 <= p <= 20.5 for p in pa) and len(set(pa)) > 1)

    print("consulta y respuesta")
    banco = Banco(Bascula(12.5, guion="normal*2,tardia:300,sin_respuesta,incompleta,invalida,normal"))
    r = [banco.consultar() for _ in range(7)]
    ok("normal: el peso", r[0][:2] == ("ok", 12.5) and r[1][:2] == ("ok", 12.5), r[:2])
    ok("tardía: llega, pero después de 300 ms", r[2][0] == "ok" and r[2][2] >= 300_000, r[2])
    ok("sin respuesta", r[3][0] == "sin_respuesta", r[3])
    ok("incompleta: bytes sin terminador", r[4][0] == "incompleta" and r[4][3] == b"+12", r[4])
    ok("inválida: formato roto", r[5][0] == "invalida", r[5])
    ok("y al acabar el guion, normal otra vez", r[6][:2] == ("ok", 12.5), r[6])
    filas = banco.cerrar()
    ok("el emulador anota cada solicitud", [f["accion"] for f in filas] ==
       ["normal", "normal", "tardia", "sin_respuesta", "incompleta", "invalida", "normal"], [f["accion"] for f in filas])
    normales = [int(f["us_respuesta"]) for f in filas if f["accion"] == "normal"]
    ok("su medición es la suya: comando → respuesta enviada", all(0 <= u < 50_000 for u in normales), normales)
    ok("sin respuesta no tiene hora de envío", filas[3]["t_enviado_ns"] == "")

    print("fallas al azar, repetibles")
    def corrida():
        b = Banco(Bascula(12.5, semilla=3, probabilidades={"sin_respuesta": 0.3, "invalida": 0.2}))
        res = [b.consultar(0.3)[0] for _ in range(20)]
        b.cerrar()
        return res
    x, y = corrida(), corrida()
    ok("con la misma semilla salen las mismas fallas", x == y, (x, y))
    ok("y salen de las dos", "sin_respuesta" in x and "invalida" in x and "ok" in x, x)

    print("envío periódico (sólo pruebas)")
    banco = Banco(Bascula(8.0), periodico_s=0.5)
    llegado = b""
    fin = time.monotonic() + 1.5
    while time.monotonic() < fin:
        llegado += banco.app.leer(0.1)
    banco.cerrar()
    ok("sin pedirlo, llegan tramas cada medio segundo", llegado.count(b"+08.0\r\n") >= 2, llegado)

    print("desconexión")
    banco = Banco(Bascula(12.5, guion="normal,desconexion:1,normal"))
    r1 = banco.consultar()
    r2 = banco.consultar(0.4)
    time.sleep(1.2)
    r3 = banco.consultar()
    banco.cerrar()
    ok("antes, el peso", r1[0] == "ok")
    ok("durante, silencio o puerto caído", r2[0] in ("sin_respuesta", "desconectado"), r2)
    ok("después de reabrir, el peso otra vez", r3[:2] == ("ok", 12.5), r3)

    print("todo bien" if not fallas else f"{fallas} fallas")
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
