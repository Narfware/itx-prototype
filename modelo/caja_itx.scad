// =====================================================================
//  Caja Mini-ITX tipo consola — modelo paramétrico (OpenSCAD 2021+)
//  Unidades: mm.  Ejes: X = ancho (0 = lado componentes, 150 = lado
//  radiador), Y = fondo (0 = frontal, 190 = trasera), Z = alto (0 = suelo).
//
//  Uso:
//   - Vista completa: deja part = "all".
//   - Exportar una pieza: pon part = "<nombre>" y F6 -> Export STL.
//     Para corte láser de un panel: part = "<panel>", flat = true,
//     F6 -> Export DXF (proyección 2D).
//   - explode > 0 separa los paneles para ver el interior.
//   - show_parts = false oculta los componentes de referencia.
// =====================================================================

/* [Vista] */
part        = "all";   // all | front | rear | side_l | side_r | top | base | tray | rad_bars | flex_cradle | gpu_rails | profile
explode     = 0;       // [0:5:80]
show_panels = true;
show_parts  = true;    // placa, GPU, radiador, Flex... (solo referencia)
flat        = false;   // true + part=<panel> -> pieza plana para exportar DXF

/* [Caja] */
W  = 150;      // ancho exterior
D  = 205;      // fondo exterior (deja ~34 mm delante del radiador para los codos de los tubos)
H  = 320;      // alto total con patas
FEET = 15;     // alto de las patas
T  = 2;        // espesor de panel (aluminio 5052)
PROF = 10;     // perfil de esquina 10 x 10
Z0 = FEET;     // cara inferior de la base
ZT = H;        // cara superior de la tapa

/* [Componentes] */
gpu_len   = 150;   // largo de la tarjeta (máx. 180 con conector arriba)
gpu_h     = 120;   // alto de la tarjeta (va en X)
gpu_thk   = 45;    // grosor (va en Z)
rad_len   = 157;   // radiador 120: largo
rad_thk   = 27;    // grosor
fan_slim  = 15;    // ventilador del radiador
pump_h    = 68;    // altura de la bomba sobre la placa

$fn = 48;
eps = 0.01;

// ---------------------------------------------------------------------
//  Posiciones (deducidas del reparto de ancho:
//  pared 2 · componentes 80 · PCB+standoffs 8 · bandeja 2 · cámara 14 ·
//  ventilador 15 · radiador 27 · pared 2)
// ---------------------------------------------------------------------
PCB_X    = 82;          // cara de componentes de la placa
PCB_T    = 1.6;
STANDOFF = 6.4;
TRAY_X   = PCB_X + PCB_T + STANDOFF;   // 90
FAN_X    = TRAY_X + T + 12;            // 104 (cámara de 12 mm)
RAD_X    = FAN_X + fan_slim;           // 119; pletinas de 2 mm entre radiador y panel
BOARD_Y0 = D - T - 3 - 170;  BOARD_Z0 = 85;   // placa 170 x 170, borde I/O a 3 mm de la trasera
GPU_Z0   = 265;                        // cara inferior de la GPU
GPU_X0   = 15;
RAD_Y0   = D - T - PROF - rad_len;      // 36: radiador contra el perfil trasero; tubos por delante
RAD_CY   = RAD_Y0 + rad_len / 2;       // centro del radiador (y del ventilador)
RAD_Z0   = 138;                        // radiador 138..258 (por encima de la bomba)
FLEX_Y0  = D - T - 10 - 150;  FLEX_Z0 = 45;          // Flex 150 x 81.5 x 40.5 (sobre la cuna, por encima del ventilador de base)
FLEX_X0  = W - T - 40.5;               // 107.5
BFAN     = 140;                        // ventilador de base 140 x 25
TRAY_Z0  = Z0 + T + 25 + 2;            // la bandeja empieza encima del ventilador de base
TRAY_Z1  = GPU_Z0 - 9;                 // y acaba bajo el travesaño de la GPU

// Agujeros mini-ITX (coordenadas en la placa, mm). VERIFICAR con la placa real.
ITX_HOLES = [[6.35, 10.16], [163.83, 33.02], [6.35, 165.10], [163.83, 165.10]];

// ---------------------------------------------------------------------
//  Utilidades
// ---------------------------------------------------------------------
module slot(l, w) { // ranura redondeada en 2D, a lo largo de Y
    hull() { translate([0, w/2]) circle(d = w); translate([0, l - w/2]) circle(d = w); }
}
module slot_band_2d(len, x0, z0, h, pitch = 8, w = 3) {
    for (x = [x0 : pitch : x0 + len]) translate([x, z0]) slot(h, w);
}
module perforated_circle_2d(r, hole = 3.2, pitch = 6) {
    intersection() {
        circle(r = r);
        for (i = [-ceil(r / pitch) : ceil(r / pitch)])
            for (j = [-ceil(r / pitch) : ceil(r / pitch)])
                translate([i * pitch + (j % 2) * pitch / 2, j * pitch * 0.866]) circle(d = hole, $fn = 12);
    }
}
module perforated_rect_2d(w, h, hole = 3.2, pitch = 6) {
    intersection() {
        square([w, h]);
        for (i = [0 : ceil(w / pitch)]) for (j = [0 : ceil(h / (pitch * 0.866))])
            translate([i * pitch + (j % 2) * pitch / 2, j * pitch * 0.866]) circle(d = hole, $fn = 12);
    }
}
module magnet_pockets_2d(w, h) { // discos de acero 8 mm en las esquinas (solo marca)
    for (p = [[12, 12], [w - 12, 12], [12, h - 12], [w - 12, h - 12]]) translate(p) circle(d = 8, $fn = 24);
}

// ---------------------------------------------------------------------
//  Paneles (cada uno se define en 2D y se extruye T mm)
// ---------------------------------------------------------------------
PANEL_H = ZT - Z0;   // 305

// Frontal (en el plano XZ, visto desde delante)
module front_2d() { // va entre la base y la tapa
    difference() {
        translate([0, T]) square([W, PANEL_H - 2 * T]);
        slot_band_2d(W - 20, 10, GPU_Z0 - Z0 + 4, 38);   // franja de la GPU
    }
}
// Trasera (en el plano XZ, visto desde delante: X igual que el modelo)
module rear_2d() {
    difference() {
        translate([0, T]) square([W, PANEL_H - 2 * T]);
        // bracket de la GPU (2 ranuras)
        translate([GPU_X0 + 3, GPU_Z0 - Z0 + 2]) square([gpu_h - 6, 41]);
        // hueco I/O 158,75 x 44,45 (borde a 2,24 mm por detrás de la cara de la placa)
        translate([PCB_X + 2.24 - 44.45, BOARD_Z0 - Z0 + 7.5]) square([44.45, 158.75]);
        // botón anti-vandálico 16 mm
        translate([25, GPU_Z0 - Z0 - 19]) circle(d = 16.2);
        // fuente Flex: ventilador + C14
        translate([FLEX_X0, FLEX_Z0 - Z0]) square([40.5, 81.5]);
    }
}
// Lateral izquierdo (lado componentes), plano YZ, Y hacia la derecha
module side_l_2d() { // va entre frontal y trasera
    difference() {
        translate([T, T]) square([D - 2 * T, PANEL_H - 2 * T]);
        slot_band_2d(D - 20, 10, GPU_Z0 - Z0 + 4, 38);
    }
}
// Lateral derecho (lado radiador), plano YZ
module side_r_2d() {
    difference() {
        translate([T, T]) square([D - 2 * T, PANEL_H - 2 * T]);
        slot_band_2d(D - 20, 10, GPU_Z0 - Z0 + 4, 38);
        translate([RAD_CY, RAD_Z0 + 60 - Z0]) perforated_circle_2d(57, 3.4, 6);
    }
}
// Tapa (plano XY)
module top_2d() {
    difference() {
        square([W, D]);
        translate([10, 10]) perforated_rect_2d(W - 20, D - 20, 3.4, 6);
    }
}
// Base (plano XY)
module base_2d() {
    difference() {
        square([W, D]);
        translate([W / 2, D / 2]) perforated_circle_2d(66, 4.2, 7);
        for (sx = [-1, 1], sy = [-1, 1]) translate([W / 2 + sx * 62.25, D / 2 + sy * 62.25]) circle(d = 4.4);
        for (p = [[13, 13], [W - 13, 13], [13, D - 13], [W - 13, D - 13]]) translate(p) circle(d = 4.4); // patas M4
    }
}

// Colocación 3D de los paneles (con explosión)
module front()  { translate([0, -explode, Z0]) rotate([90, 0, 0]) translate([0, 0, -T]) linear_extrude(T) front_2d(); }
module rear()   { translate([0, D - T + explode, Z0]) rotate([90, 0, 0]) translate([0, 0, -T]) linear_extrude(T) rear_2d(); }
module side_l() { translate([-explode, 0, Z0]) rotate([90, 0, 90]) linear_extrude(T) side_l_2d(); }
module side_r() { translate([W - T + explode, 0, Z0]) rotate([90, 0, 90]) linear_extrude(T) side_r_2d(); }
module top()    { translate([0, 0, ZT - T + explode]) linear_extrude(T) top_2d(); }
module base()   { translate([0, 0, Z0 - explode]) linear_extrude(T) base_2d(); }

// ---------------------------------------------------------------------
//  Esqueleto
// ---------------------------------------------------------------------
module profile(len = PANEL_H - 2 * T) { // perfil 10 x 10 con alojamientos para imanes 6 x 3
    difference() {
        cube([PROF, PROF, len]);
        for (z = [12, len - 12]) {
            translate([PROF / 2, -eps, z]) rotate([-90, 0, 0]) cylinder(d = 6.2, h = 3);
            translate([-eps, PROF / 2, z]) rotate([0, 90, 0]) cylinder(d = 6.2, h = 3);
        }
    }
}
module skeleton() {
    color("#3A3F46")
    for (x = [T, W - T - PROF], y = [T, D - T - PROF])
        if (x > W / 2 && y > D / 2) {
            // trasero derecho: se corta a la altura de la Flex; el collarín hace de esquina
            z1 = FLEX_Z0 + 81.5 + T + 2;
            translate([x, y, z1]) profile(ZT - T - z1);
        } else translate([x, y, Z0 + T]) profile();
}

// ---------------------------------------------------------------------
//  Piezas internas
// ---------------------------------------------------------------------
// Bandeja central: placa sobre standoffs, ventanas para backplate y tubos
module tray() {
    color("#5B626B") difference() {
        translate([TRAY_X, T + PROF, TRAY_Z0]) cube([T, D - 2 * (T + PROF), TRAY_Z1 - TRAY_Z0]);
        // ventana backplate CPU (centrada en la placa, ajustar al socket)
        translate([TRAY_X - eps, BOARD_Y0 + 45, BOARD_Z0 + 45]) cube([T + 2 * eps, 80, 80]);
        // ventana de tubos bajo la placa
        translate([TRAY_X - eps, T + PROF + 2, TRAY_Z0 + 4]) cube([T + 2 * eps, 60, BOARD_Z0 - TRAY_Z0 - 6]); // paso de tubos por delante
    }
    // standoffs M3
    color("#C9A227") for (h = ITX_HOLES)
        translate([PCB_X + PCB_T, BOARD_Y0 + h[0], BOARD_Z0 + h[1]]) rotate([0, 90, 0]) cylinder(d = 5.5, h = STANDOFF, $fn = 6);
}
// Pletinas del radiador: dos tiras de 15 x 2 mm por la cara exterior del radiador,
// atornilladas a sus agujeros de 105 mm y a los perfiles delantero y trasero.
// El ventilador va atornillado al radiador por dentro (sin marco).
module rad_bars() {
    color("#5B626B") for (sz = [-1, 1]) difference() {
        translate([RAD_X + rad_thk, T + PROF, RAD_Z0 + 60 + sz * 52.5 - 7.5]) cube([T, D - 2 * (T + PROF), 15]);
        for (sy = [-1, 1]) translate([RAD_X + rad_thk - eps, RAD_CY + sy * 52.5, RAD_Z0 + 60 + sz * 52.5]) rotate([0, 90, 0]) cylinder(d = 4.4, h = T + 2 * eps);
    }
}
// Cuna de la Flex + collarín hasta la trasera
module flex_cradle() {
    color("#5B626B") {
        translate([FLEX_X0, FLEX_Y0, FLEX_Z0 - T]) cube([40.5, 150, T]);
        difference() { // collarín
            translate([FLEX_X0 - T, FLEX_Y0 + 150, FLEX_Z0 - T]) cube([40.5 + T, D - T - FLEX_Y0 - 150, 81.5 + 2 * T]);
            translate([FLEX_X0, FLEX_Y0 + 150 - eps, FLEX_Z0]) cube([40.5 - eps, D, 81.5]);
        }
    }
}
// Raíles de la GPU: dos perfiles en L bajo los cantos largos de la tarjeta,
// de perfil delantero a trasero, con tira de goma. El del lado del PCIe
// lleva la pinza del zócalo del riser. El centro queda libre para que
// respiren los ventiladores de la gráfica.
module gpu_rails() {
    color("#8A9099") for (x = [GPU_X0, GPU_X0 + gpu_h - 8]) translate([x, T + PROF, GPU_Z0 - 6]) {
        cube([8, D - 2 * (T + PROF), 2]);
        translate([x < W / 2 ? 0 : 6, 0, 0]) cube([2, D - 2 * (T + PROF), 6]);
    }
    color("#8A9099") translate([GPU_X0 + 8, D - T - 125, GPU_Z0 - 6]) cube([20, 90, 2]); // pinza del riser
}

// ---------------------------------------------------------------------
//  Componentes de referencia (no se fabrican)
// ---------------------------------------------------------------------
module ref_parts() {
    // placa Mini-ITX (boca abajo, slot arriba)
    color("#2F5A2F") translate([PCB_X, BOARD_Y0, BOARD_Z0]) cube([PCB_T, 170, 170]);
    // bomba AIO
    color("#2A2E33") translate([PCB_X - pump_h, BOARD_Y0 + 55, BOARD_Z0 + 55]) cube([pump_h, 60, 60]);
    // GPU (tumbada, ventiladores abajo)
    color("#7A3E22", 0.9) translate([GPU_X0, D - T - gpu_len, GPU_Z0]) cube([gpu_h, gpu_len, gpu_thk]);
    color("#555", 0.4) translate([GPU_X0, D - T - 180, GPU_Z0]) cube([gpu_h, 180, gpu_thk]); // contorno 180
    // radiador + ventilador
    color("#24406E") translate([RAD_X, RAD_Y0, RAD_Z0]) cube([rad_thk, rad_len, 120]);
    color("#3D5A8A") translate([FAN_X, RAD_CY - 60, RAD_Z0]) cube([fan_slim, 120, 120]);
    // tubos del AIO: salen por delante del radiador y bajan hasta la ventana de la bandeja
    color("#111") for (dz = [20, 45]) translate([RAD_X + 10, T + PROF + 2, RAD_Z0 + dz - 10]) cube([12, RAD_Y0 - T - PROF - 2, 12]);
    // Flex
    color("#44484E") translate([FLEX_X0, FLEX_Y0, FLEX_Z0]) cube([40.5, 150, 81.5]);
    // ventilador de base 140 x 25
    color("#3D5A8A") translate([(W - BFAN) / 2, (D - BFAN) / 2, Z0 + T]) cube([BFAN, BFAN, 25]);
    // patas
    color("#111") for (p = [[13, 13], [W - 13, 13], [13, D - 13], [W - 13, D - 13]]) translate([p[0], p[1], 0]) cylinder(d = 18, h = FEET);
}

// ---------------------------------------------------------------------
//  Montaje
// ---------------------------------------------------------------------
module panels() {
    color("#1E2125") { front(); rear(); side_l(); side_r(); top(); base(); }
}
module assembly() {
    skeleton();
    tray();
    rad_bars();
    flex_cradle();
    gpu_rails();
    if (show_parts) ref_parts();
    if (show_panels) panels();
}

module flat_part(name) {
    if (name == "front")  front_2d();
    if (name == "rear")   rear_2d();
    if (name == "side_l") side_l_2d();
    if (name == "side_r") side_r_2d();
    if (name == "top")    top_2d();
    if (name == "base")   base_2d();
}

if (part == "all") assembly();
else if (flat) flat_part(part);
else {
    if (part == "front")       front();
    if (part == "rear")        rear();
    if (part == "side_l")      side_l();
    if (part == "side_r")      side_r();
    if (part == "top")         top();
    if (part == "base")        base();
    if (part == "tray")        tray();
    if (part == "rad_bars")    rad_bars();
    if (part == "flex_cradle") flex_cradle();
    if (part == "gpu_rails")   gpu_rails();
    if (part == "profile")     profile();
}
