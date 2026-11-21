# Primera medición en hardware, 30/10/2026 (20:46–20:55)

Emulador en la Raspberry Pi Zero 2 W (`edgelab-zero2w`, gadget USB serial,
`/dev/ttyGS0`, enlace USB high-speed), montada en un adaptador USB-A y
conectada a un hub USB-C de la Mac (MacBook Pro M5 Pro), que la ve como
`/dev/cu.usbmodem1301`. Entorno completo en `entorno.txt`. Una sola corrida
por modo, un solo equipo, un solo hub: es lo que pasó aquí, no un promedio de
equipos. El terminador CR LF es un supuesto nuestro.

Las dos mediciones no se mezclan:

- `emulador-*.csv`, medido en la Pi: de recibir la `P` a que la respuesta
  terminó de salir (tcdrain).
- `cliente-*.csv`, medido en la Mac: de antes de mandar la `P` a recibir el
  terminador, con USB, hub y lectura incluidos. Límite de espera: 1.0 s.

## Modo normal — 1,000 consultas cada 0.1 s, peso 12.5 ± 0.3, semilla 1

| | n | mediana | p95 | máx |
|---|---|---|---|---|
| Emulador (Pi) | 1000 | 0.158 ms | 0.291 ms | 0.347 ms |
| Aplicación (Mac), ok | 1000 | 0.472 ms | 0.661 ms | 0.944 ms |

1,000 de 1,000 correctas.

## Modo de fallas — 300 consultas, semilla 7, al azar: tardía 10 % (800 ms), sin respuesta 5 %, incompleta 5 %, inválida 5 %

| Lo que hizo el emulador | n | Lo que vio la aplicación | mediana en la Mac |
|---|---|---|---|
| normal | 210 | ok | 0.518 ms |
| tardía (800 ms) | 41 | **ok** | 800.8 ms |
| sin respuesta | 21 | sin_respuesta | 1004.6 ms (el límite) |
| incompleta (`+12`) | 13 | incompleta | 1004.1 ms (el límite) |
| inválida (`+1?.5`) | 15 | invalida | 0.501 ms |

Cada falla se clasificó como lo que era (300 de 300, emparejadas por orden).
Lo que enseña: las 41 tardías cuentan como «ok». Un contador de éxitos no las
ve; el p95 de las «ok» sí (0.55 ms de mediana, 800.8 ms de p95). Y una trama
incompleta cuesta lo mismo que el silencio: la aplicación espera el límite
entero.

## Lo que no se midió

- Desconexión física del cable (hay que desenchufarlo a mano durante una
  corrida). La desconexión del emulador cierra el puerto, pero el enlace USB
  sigue arriba: la Mac ve silencio, no un puerto que desaparece.
- Windows y sus nombres de puerto COM.
- Otros hubs, otros cables, otras computadoras.

Temperatura de la Pi al terminar: 44.0 °C, sin throttling (0x0).
