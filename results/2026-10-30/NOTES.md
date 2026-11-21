# Results, October 30, 2026 (English summary)

The `LEEME.md` files next to each run are the full notes, in Spanish. Setup: a
Raspberry Pi Zero 2 W (Raspberry Pi OS on Debian 13, kernel 6.18) in USB
gadget mode on a USB-A adapter, plugged into a USB-C hub on a MacBook Pro
(macOS 27). `entorno.txt` has the details. One setup, one run per mode.

| Folder / files | What | Result |
|---|---|---|
| `emulador-normal.csv`, `cliente-normal.csv` | 1,000 requests every 0.1 s, weight 12.5 ± 0.3, seed 1 | 1,000/1,000 valid. Emulator (Pi) median 0.158 ms, p95 0.291, max 0.347. Application (Mac) median 0.472 ms, p95 0.661, max 0.944 |
| `emulador-fallas.csv`, `cliente-fallas.csv` | 300 requests, seed 7, random faults (late 10 %, none 5 %, incomplete 5 %, invalid 5 %) | 210 normal, 41 late, 21 none, 13 incomplete, 15 invalid; all 300 classified correctly. Late ones count as valid (median 800.8 ms on the Mac); none and incomplete take the full 1 s limit; invalid is caught in 0.5 ms |
| `cable/` | Physical unplug, with the Pi on a separate power supply | Not measured. After the first unplug the Mac lost the hub on every port; without the Pi the hub came back. Probably the Pi back-feeding 5 V into the hub (not verified). The Pi's USB controller stayed `configured` throughout |
| `software-1/` | 3 software cuts of 5 s (`soltar.sh 3 5 20`) | The test client crashed on the 2nd cut: `termios.error` from `tcflush`, not an `OSError`. Fixed in `transporte.py` |
| `software-2/` | Same, fixed client | 3/3 survived. Mac without the port 5.59 / 5.65 / 5.44 s; application blind 6.04 / 6.04 / 5.54 s (Mac clock). Pi configured again 0.36 / 0.43 / 0.22 s after taking the line back (Pi clock). 2,997 valid requests |

Not measured: a real cable unplug, Windows, other hubs, cables or computers.
