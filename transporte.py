"""Transporte: abrir un puerto serial y mover bytes. No sabe nada de básculas.

Sirve igual para /dev/ttyGS0 (la Pi en modo gadget USB), para el puerto que
ve la computadora (/dev/tty.usbmodem… en macOS, /dev/ttyACM0 en Linux) y para
un pseudoterminal en las pruebas. Sólo biblioteca estándar (termios): corre en
la Pi Zero 2 W sin instalar nada.

Configuración: 9600 baudios, 8 bits, sin paridad, 1 bit de parada (9600 8N1),
modo crudo. Por USB CDC ACM la velocidad no limita nada: viaja a la del USB;
se fija igual porque es lo que la aplicación espera abrir.
"""
from __future__ import annotations

import os
import select
import termios
import time
import tty


def _termios(fn, *args):
    """termios.error no es OSError: si el dispositivo se va a media llamada
    (ENXIO al desenchufar), se convierte para que quien llama lo trate como
    cualquier otra falla del puerto. Sin esto, el cliente se cayó entero en la
    segunda desconexión del 30/10 (la primera le tocó en un read y sí la libró).
    """
    try:
        return fn(*args)
    except termios.error as e:
        raise OSError(*e.args) from e


class Puerto:
    def __init__(self, ruta: str | None = None, fd: int | None = None, baudios: int = 9600):
        self.ruta = ruta
        self.fd = fd if fd is not None else os.open(ruta, os.O_RDWR | os.O_NOCTTY)
        if os.isatty(self.fd):
            self._configurar(baudios)

    def _configurar(self, baudios: int) -> None:
        tty.setraw(self.fd)
        a = _termios(termios.tcgetattr, self.fd)
        velocidad = getattr(termios, f"B{baudios}")
        a[4] = a[5] = velocidad                                   # entrada y salida
        a[2] &= ~(termios.PARENB | termios.CSTOPB | termios.CSIZE)  # sin paridad, 1 de parada
        a[2] |= termios.CS8 | termios.CREAD | termios.CLOCAL        # 8 bits
        _termios(termios.tcsetattr, self.fd, termios.TCSANOW, a)

    def leer(self, espera_s: float) -> bytes:
        """Lo que haya llegado en a lo más espera_s segundos (b'' si nada)."""
        listo, _, _ = select.select([self.fd], [], [], espera_s)
        if not listo:
            return b""
        datos = os.read(self.fd, 256)
        if datos == b"":
            raise ConnectionError("el otro lado cerró el puerto")
        return datos

    def escribir(self, datos: bytes, drenar: bool = True) -> None:
        """Escribe todo y, con drenar, espera a que salga del búfer (tcdrain).

        El emulador drena: su medición termina cuando la respuesta salió. La
        aplicación no lo necesita para mandar una `P`, y no debe hacerlo: en un
        pseudoterminal, tcdrain espera a que el otro lado lea, y si los dos
        drenan a la vez se quedan esperándose (pasó en las pruebas).
        """
        vista = memoryview(datos)
        while vista:
            n = os.write(self.fd, vista)
            vista = vista[n:]
        if drenar and os.isatty(self.fd):
            _termios(termios.tcdrain, self.fd)

    def descartar(self) -> None:
        """Tira lo pendiente de leer: un cliente lo hace antes de una consulta nueva."""
        if os.isatty(self.fd):
            _termios(termios.tcflush, self.fd, termios.TCIFLUSH)

    def cerrar(self) -> None:
        try:
            os.close(self.fd)
        except OSError:
            pass


def ahora_ns() -> int:
    return time.monotonic_ns()
