# Desconexión por software, intento 1 (30/10/2026, 21:52): la aplicación se cayó

La Pi alimentada sólo por el adaptador USB-A, en el hub de la Mac
(`/dev/cu.usbmodem11301`). `soltar.sh 3 5 20` (con sudo, lo corrió Israel):
la Pi suelta la línea USB (`soft_connect`) 5 s, la retoma y espera 20 s; tres
veces. Para la Mac es una desconexión real; la Pi sigue prendida.

- Primera desconexión: el cliente pierde el puerto, lo reabre a los 6.04 s y
  sigue (consultas 295 y 296).
- Segunda: **el cliente se cae entero** (`cliente.log`, al final). El
  desenchufe le tocó en `tcflush` (vaciar el búfer antes de preguntar), que
  lanza `termios.error`, no `OSError`, y nadie lo atrapaba. En la primera le
  había tocado en un `read`, que sí estaba cubierto. Si la aplicación sobrevive
  o no depende del instante en que se va el cable.
- Corregido en `transporte.py` (`_termios` convierte el error); repetido en
  `software-2`. No hay `cliente.csv` porque el proceso murió antes de
  escribirlo; el log tiene las 476 consultas correctas previas.

Lo demás de esta corrida (Pi y Mac) coincide con `software-2`.
