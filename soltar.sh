#!/bin/bash
# Suelta y retoma la línea USB del gadget, como si se desenchufara el cable
# (para la Mac es una desconexión real; la Pi sigue prendida). Con sudo:
#     sudo bash soltar.sh [veces] [segundos_fuera] [segundos_entre]
# Anota cada cambio con el reloj de la Pi en r3/soltar.csv (junto a este script).
set -euo pipefail
VECES=${1:-3}; FUERA=${2:-5}; ENTRE=${3:-20}
UDC=$(ls /sys/class/udc | head -1)
AQUI=$(cd "$(dirname "$0")" && pwd)
OUT="$AQUI/r3/soltar.csv"
mkdir -p "$AQUI/r3"
[ -f "$OUT" ] || echo "t_reloj,accion" > "$OUT"
for i in $(seq 1 "$VECES"); do
  echo "$(date +%s.%N),desconecta" >> "$OUT"
  echo disconnect > "/sys/class/udc/$UDC/soft_connect"
  echo "$i/$VECES fuera ${FUERA}s"
  sleep "$FUERA"
  echo "$(date +%s.%N),conecta" >> "$OUT"
  echo connect > "/sys/class/udc/$UDC/soft_connect"
  [ "$i" -lt "$VECES" ] && sleep "$ENTRE"
done
chown --reference="$AQUI" "$OUT"
echo "listo: $OUT"
