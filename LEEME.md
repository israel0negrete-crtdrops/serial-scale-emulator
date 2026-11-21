# La báscula que era una Raspberry: el emulador

Una Raspberry Pi Zero 2 W que, conectada por USB, se presenta ante la
computadora como un puerto serial y contesta como una báscula. Protocolo
didáctico inspirado en el de una báscula comercial (sin la marca y sin
pretender reproducirlo entero): la aplicación manda `P` y la báscula contesta
`+12.5` con CR LF (el terminador es un supuesto nuestro). 9600 8N1.

Sólo biblioteca estándar de Python. Tres capas separadas:

| Archivo | Capa | Qué hace |
|---|---|---|
| `transporte.py` | transporte | abre el puerto (gadget USB, el de la computadora o un pty) y mueve bytes |
| `protocolo.py` | protocolo | la `P`, la trama del peso y cómo la valida la aplicación |
| `comportamiento.py` | comportamiento | el peso (fijo o fluctuante) y las fallas, por guion o al azar con semilla |
| `emulador.py` | — | la báscula: junta las tres y anota, de su lado, comando → respuesta enviada |
| `cliente.py` | — | la aplicación: consulta, clasifica y mide desde la computadora |
| `prueba.py` | — | 25 pruebas sin hardware, sobre un pseudoterminal |

Las dos mediciones no se mezclan: `emulador.py --registro` mide en la Pi
(del comando recibido a la respuesta enviada); `cliente.py --registro` mide en
la computadora (de mandar la `P` a recibir el terminador, USB incluido).
