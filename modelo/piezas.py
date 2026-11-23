"""Cajas envolventes de cada pieza, con las mismas cotas que caja_itx.scad.

Se usa para comprobar choques entre piezas y para generar piezas.json,
que lee el visor 3D (modelo.html). Si cambias una cota en el .scad,
cámbiala aquí también y vuelve a ejecutar:  python3 piezas.py
"""
import itertools, json, pathlib

W, D, H, FEET, T, PROF = 150, 190, 320, 15, 2, 10
Z0, ZT = FEET, H
PCB_X, PCB_T, STANDOFF = 82, 1.6, 6.4
TRAY_X = PCB_X + PCB_T + STANDOFF
FAN_X = TRAY_X + T + 14
RAD_X = FAN_X + 15
BOARD_Y0, BOARD_Z0 = 15, 85
GPU_Z0, GPU_X0, GPU_H, GPU_T = 265, 15, 120, 45
RAD_Y0, RAD_Z0 = (D - 157) / 2, 138
FLEX_X0, FLEX_Y0, FLEX_Z0 = W - T - 40.5, 28, 45
BF = 140

parts = []
def box(name, group, color, x, y, z, dx, dy, dz, check=True):
    parts.append(dict(name=name, group=group, color=color, p=[x, y, z], s=[dx, dy, dz], check=check))

# Paneles
box("Frontal", "panel", "#1E2125", 0, 0, Z0 + T, W, T, ZT - Z0 - 2 * T)
box("Trasera", "panel", "#1E2125", 0, D - T, Z0 + T, W, T, ZT - Z0 - 2 * T)
box("Lateral componentes", "panel", "#1E2125", 0, T, Z0 + T, T, D - 2 * T, ZT - Z0 - 2 * T)
box("Lateral radiador", "panel", "#1E2125", W - T, T, Z0 + T, T, D - 2 * T, ZT - Z0 - 2 * T)
box("Tapa", "panel", "#1E2125", 0, 0, ZT - T, W, D, T)
box("Base", "panel", "#1E2125", 0, 0, Z0, W, D, T)
# Esqueleto
for x, y in itertools.product([T, W - T - PROF], [T, D - T - PROF]):
    if x > W / 2 and y > D / 2:
        z1 = FLEX_Z0 + 81.5 + T + 2
        box("Perfil 10×10", "esqueleto", "#3A3F46", x, y, z1, PROF, PROF, ZT - T - z1)
    else:
        box("Perfil 10×10", "esqueleto", "#3A3F46", x, y, Z0 + T, PROF, PROF, ZT - Z0 - 2 * T)
# Piezas internas
TRAY_Z0, TRAY_Z1 = Z0 + T + 25 + 2, GPU_Z0 - 9
box("Bandeja central", "interno", "#5B626B", TRAY_X, T + PROF, TRAY_Z0, T, D - 2 * (T + PROF), TRAY_Z1 - TRAY_Z0)
box("Marco del radiador", "interno", "#5B626B", FAN_X - T, T + PROF, RAD_Z0 - 4, T, D - 2 * (T + PROF), 122)
box("Cuna de la Flex", "interno", "#5B626B", FLEX_X0, FLEX_Y0, FLEX_Z0 - T, 40.5, 150, T)
box("Collarín de la Flex", "interno", "#5B626B", FLEX_X0 - T, FLEX_Y0 + 150, FLEX_Z0 - T, 40.5 + T, D - T - FLEX_Y0 - 150, 81.5 + 2 * T, check=False)
box("Travesaño GPU", "interno", "#8A9099", GPU_X0, D - T - 150 - 2, GPU_Z0 - 6, GPU_H, 12, 6)
box("Soporte del riser", "interno", "#8A9099", GPU_X0 + 10, D - T - 140, GPU_Z0 - 8, 60, 100, 2)
# Componentes de referencia
box("Placa Mini-ITX", "componente", "#2F5A2F", PCB_X, BOARD_Y0, BOARD_Z0, PCB_T, 170, 170)
box("Bomba AIO", "componente", "#2A2E33", PCB_X - 68, BOARD_Y0 + 55, BOARD_Z0 + 55, 68, 60, 60)
box("GPU (150 mm)", "componente", "#7A3E22", GPU_X0, D - T - 150, GPU_Z0, GPU_H, 150, GPU_T)
box("Contorno GPU 180 mm", "contorno", "#FF8A55", GPU_X0, D - T - 180, GPU_Z0, GPU_H, 180, GPU_T, check=False)
box("Radiador 120", "componente", "#24406E", RAD_X, RAD_Y0, RAD_Z0, 27, 157, 120)
box("Ventilador radiador 120×15", "componente", "#3D5A8A", FAN_X, D / 2 - 60, RAD_Z0, 15, 120, 120)
box("Fuente Flex", "componente", "#44484E", FLEX_X0, FLEX_Y0, FLEX_Z0, 40.5, 150, 81.5)
box("Ventilador base 140×25", "componente", "#3D5A8A", (W - BF) / 2, (D - BF) / 2, Z0 + T, BF, BF, 25)
for x, y in [(13, 13), (W - 13, 13), (13, D - 13), (W - 13, D - 13)]:
    box("Pata", "pata", "#111111", x - 9, y - 9, 0, 18, 18, FEET, check=False)

def overlap(a, b):
    v = 1.0
    for i in range(3):
        lo = max(a["p"][i], b["p"][i]); hi = min(a["p"][i] + a["s"][i], b["p"][i] + b["s"][i])
        if hi - lo <= 0.05:
            return 0
        v *= hi - lo
    return v

if __name__ == "__main__":
    clashes = []
    for a, b in itertools.combinations([p for p in parts if p["check"]], 2):
        v = overlap(a, b)
        if v:
            clashes.append((a["name"], b["name"], round(v)))
    # Panels touching skeleton/tray at faces are not clashes (overlap 0 by tolerance)
    print("Choques:", clashes if clashes else "ninguno")
    out = pathlib.Path(__file__).with_name("piezas.json")
    out.write_text(json.dumps(dict(dims=[W, D, H], parts=parts), ensure_ascii=False, indent=1))
    print("piezas.json:", len(parts), "piezas")
