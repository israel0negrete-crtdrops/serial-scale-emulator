# Desconexión por software, intento 2 (30/10/2026, 21:56–22:01)

Igual que `software-1`, con el cliente corregido. 3,000 consultas cada 0.1 s,
límite 1 s; al perder el puerto, el cliente intenta reabrirlo cada 0.5 s.
Cada lado con su reloj; no se restan horas de un equipo contra el otro.

## Pi (`soltar.csv`, `vigia-pi.csv`, `emulador.log`)

| | 1 | 2 | 3 |
|---|---|---|---|
| soltar → UDC `not attached` | 7.5 ms | 10.4 ms | 12.0 ms |
| retomar → UDC `configured` (la Mac la volvió a enumerar) | 0.363 s | 0.426 s | 0.223 s |

El emulador se entera de la caída: Linux le cuelga `/dev/ttyGS0` (lectura
vacía, ~2 ms después de soltar). Reabre el puerto a los 0.4 s, pero eso no
dice que el anfitrión haya vuelto. Quien sí lo marca es el controlador USB
(`configured` en `vigia-pi.csv`); el emulador, leyendo su puerto, no.

## Mac (`vigia-mac.csv`, `cliente.csv`)

| | 1 | 2 | 3 |
|---|---|---|---|
| puerto ausente (la Pi lo soltó 5.0 s) | 5.588 s | 5.648 s | 5.444 s |
| cliente ciego (de perder el puerto a reabrirlo) | 6.04 s | 6.04 s | 5.54 s |
| primera consulta tras volver | ok, 0.61 ms | ok, 0.75 ms | ok, 0.73 ms |

2,997 correctas (mediana 0.61 ms, p95 0.73 ms, máx 4.45 ms) y 3
desconectadas; el emulador contestó las 2,997 solicitudes que le llegaron.
El cliente queda ciego entre 0.5 y algo más de 1 s más que el corte de 5 s configurado: unas décimas de
volver a presentarse y hasta 0.5 s de su propio intervalo de reintento.

Alcance: una Pi, un hub, una Mac, tres cortes de 5 s. La desconexión física
del cable con la Pi en fuente aparte no se pudo medir (ver `../cable/`).
