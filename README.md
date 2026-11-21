# Serial scale emulator

A Raspberry Pi Zero 2 W that, plugged in over USB, shows up on the computer as
a serial port and answers like a scale. Built to work on an application's
integration without depending on the real device all the time, and to make
the scale fail on purpose: late answers, no answer, half a frame, a broken
frame, and disconnections.

Note: [The scale that was a Raspberry Pi](https://crtdrops.mx/notas/the-scale-that-was-a-raspberry-pi.html)
(Spanish: [La báscula que era una Raspberry](https://crtdrops.mx/notas/la-bascula-que-era-una-raspberry.html)).

The code and its comments are in Spanish; this README and
`results/2026-10-30/NOTES.md` are in English.

## The protocol

Generic, shaped like the one of a commercial scale, without its brand and
without claiming to reproduce it fully: serial 9600 8N1, the application sends
`P`, the scale answers `+12.5`. The `\r\n` terminator is **an assumption**:
the original one is not confirmed. Over the USB gadget the baud rate does not
apply (bytes travel at USB speed); the port is configured that way because it
is what the application expects to open.

## Three layers

Python standard library only: it runs on the Pi Zero without installing
anything.

| File | Layer | What it does |
|---|---|---|
| `transporte.py` | transport | opens the port (USB gadget, the computer's port, or a pty) and moves bytes |
| `protocolo.py` | protocol | the `P`, the weight frame and how the application validates it |
| `comportamiento.py` | behavior | the weight (fixed or fluctuating) and the faults, scripted or random with a seed |
| `emulador.py` | — | the scale: puts the three together and logs, on its side, command → answer sent |
| `cliente.py` | — | the application: queries, classifies and measures from the computer |
| `vigia.py` | — | logs when the USB link drops and comes back, on each side, with that side's clock |
| `soltar.sh` | — | makes the Pi let go of the USB line and take it back (an unplug, for the computer) |
| `prueba.py` | — | 25 tests without hardware; the query tests run over a pseudoterminal |

Fault actions (`--guion` for a scripted sequence, `--azar` for random with
`--semilla`): `normal`, `tardia:MS`, `sin_respuesta`, `incompleta`,
`invalida`, `desconexion:S`.

```bash
python3 prueba.py                                   # anywhere, no hardware
python3 emulador.py --puerto /dev/ttyGS0 --registro e.csv \
    --guion "normal*5,tardia:800,sin_respuesta,incompleta,invalida"   # on the Pi
python3 cliente.py --puerto /dev/cu.usbmodem11301 --veces 200 --registro c.csv  # on the computer
```

## Two measurements that don't mix

- `emulador.py --registro`, on the Pi: from receiving the `P` until the answer
  has finished going out.
- `cliente.py --registro`, on the computer: from just before sending the `P`
  until the terminator arrives, USB and OS read included.

Each one uses its own machine's clock. They are never added or subtracted.

## Pi Zero 2 W setup (USB gadget serial)

With sudo, once, on Raspberry Pi OS (Debian 13):

- `/boot/firmware/config.txt`, in the `[all]` section:
  `dtoverlay=dwc2,dr_mode=peripheral`. Careful: the stock file already has a
  `dtoverlay=dwc2,dr_mode=host` line under `[cm5]`; searching for
  "dtoverlay=dwc2" alone gives a false "already there".
- `/etc/modules-load.d/`: `dwc2` and `g_serial`.
- `systemctl mask serial-getty@ttyGS0.service`, so no console opens on the port.
- The user that runs the emulator in the `dialout` group. Reboot.

Plug the Pi's **data** port (the middle one) into the computer. **Do not also
power it through the PWR port while it is plugged into a hub:** in our test the
Mac stopped seeing the hub on any port (see `results/2026-10-30/cable/`).

## What was measured (October 30, 2026)

One Pi Zero 2 W on a USB-A adapter, one USB-C hub, one MacBook Pro (macOS 27).
Details and caveats in `results/2026-10-30/NOTES.md`.

- **Normal, 1,000 requests:** all valid. Emulator 0.16 ms median (Pi);
  application 0.47 ms median (Mac). This measures the emulator over USB, not
  a scale: at a real 9600 baud the 7-byte frame alone takes about 7 ms.
- **Faults, 300 requests:** every one classified as what it was. The 41 late
  answers count as valid; only latency shows them. An incomplete frame costs
  the full 1 s limit, like silence.
- **Software disconnection, 3 cuts of 5 s:** the first test client crashed on
  the second cut (`termios.error` is not an `OSError`); fixed, the second run
  survived all three, with the application blind 5.5–6.0 s per cut.

## License

MIT.
