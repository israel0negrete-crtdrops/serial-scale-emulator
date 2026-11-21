# Prueba del cable, 30/10/2026 (21:04–21:36): no se pudo medir la reconexión

Montaje: la Pi Zero 2 W con una fuente micro-USB en el puerto PWR (para que no
se apagara al desenchufar) y el adaptador USB-A en un hub USB-C (Genesys Logic,
05e3:0610/0626) conectado a la Mac. Emulador y vigía en la Pi, cliente
(consulta cada 0.1 s, límite 1 s, reintento de abrir 60 s) y vigía en la Mac.

## Lo que pasó

- 1,352 consultas correctas (mediana 0.61 ms, p95 0.73 ms, máx 5.56 ms).
- 21:06:31: primer desenchufe. La Mac pierde `/dev/cu.usbmodem21301`
  (`vigia-mac.csv`) y el cliente lo marca `desconectado`.
- Los dos desenchufes siguientes no se registran: la Mac nunca volvió a ver la
  Pi, y después tampoco el hub, en ningún puerto.
- En la Pi, el kernel no anotó nada en todo ese tiempo (ni salida ni
  enumeración nueva) y el UDC siguió en `configured` (`vigia-pi.csv`): el
  dwc2 de la Zero no se entera de que el anfitrión se fue. La Pi no se apagó.
- 21:36: sin el adaptador de la Pi, el hub vuelve a aparecer en la Mac.

## Lo que creemos (no confirmado del todo)

En la Pi Zero, el PWR y el VBUS del puerto de datos son la misma línea de 5 V.
Con la fuente puesta, la Pi empuja 5 V hacia el hub por el adaptador, y la Mac
deja de aceptar el hub. Confirmado a medias: sin la Pi, el hub aparece; la
otra mitad (volver a meterla con la fuente y ver que el hub desaparece) no se
hizo para no meterle voltaje al puerto de la Mac otra vez.

## Lo que queda

Medir la desconexión con la Pi alimentada sólo por el adaptador: por software
(soltar y retomar la línea USB desde la Pi, con sudo) o con un adaptador que
corte VBUS y deje pasar datos («USB power blocker») para el cable real.
