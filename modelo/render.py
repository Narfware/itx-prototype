"""Render de la caja sobre un escritorio: trazador de rayos en numpy.

Escena en mm, eje Y hacia arriba. Primitivas: cajas alineadas y cilindros
verticales. Sombras suaves de una luz de área, oclusión ambiental y
texturas procedurales (rejillas, ranuras, veta de la madera).
"""
import sys, time
import numpy as np

W_IMG, H_IMG = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (480, 270)
SPP = int(sys.argv[3]) if len(sys.argv) > 3 else 1
OUT = sys.argv[4] if len(sys.argv) > 4 else "/home/claude/render/out.png"
rng = np.random.default_rng(7)

# ---------------- escena ----------------
boxes = []   # (min, max, mat)
cyls = []    # (cx, cz, r, y0, y1, mat)
def box(mn, mx, mat): boxes.append((np.array(mn, float), np.array(mx, float), mat))

# materiales
DESK, WALL, CASE, RUBBER, MON, SCREEN, KEYB, MUG, BOOK1, BOOK2, STAND, PAD = range(12)

box([-2600, -40, -520], [2600, 0, 900], DESK)
box([-4000, -400, -560], [4000, 3000, -520], WALL)
CX0, CX1, CZ0, CZ1, CY0, CY1 = 250, 400, -102.5, 102.5, 15, 320
DEPTH = CZ1 - CZ0; RAD_U = 2 + 34 + 157 / 2   # centro del radiador medido desde el frontal
box([CX0, CY0, CZ0], [CX1, CY1, CZ1], CASE)
for x, z in [(CX0 + 4, CZ0 + 4), (CX1 - 22, CZ0 + 4), (CX0 + 4, CZ1 - 22), (CX1 - 22, CZ1 - 22)]:
    box([x, 0, z], [x + 18, 15, z + 18], RUBBER)
# monitor 27": pantalla 597 x 336, marco fino
MX0, MX1, MY0, MY1, MZ = -560, 60, 150, 505, -240
box([MX0, MY0, MZ - 22], [MX1, MY1, MZ], MON)
box([MX0 + 8, MY0 + 22, MZ + 0.01], [MX1 - 8, MY1 - 8, MZ + 0.6], SCREEN)
box([-275, 40, MZ - 60], [-225, 200, MZ - 30], STAND)
box([-380, 0, MZ - 150], [-120, 12, MZ + 40], STAND)
# alfombrilla, teclado, ratón
box([-640, 0, -40], [160, 3, 300], PAD)
box([-500, 3, 40], [-60, 22, 175], KEYB)
# libros y taza
box([-1000, 0, -300], [-760, 38, -110], BOOK1)
box([-985, 38, -290], [-775, 66, -120], BOOK2)
cyls.append((-860, -205, 42, 66, 160, MUG))

# ---------------- cámara ----------------
eye = np.array([820.0, 470.0, 980.0]); look = np.array([110.0, 205.0, 0.0])
fov = np.radians(33)
fwd = look - eye; fwd /= np.linalg.norm(fwd)
right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right)
up = np.cross(right, fwd)

LIGHT_C = np.array([1500.0, 2100.0, 1400.0]); LIGHT_R = 450.0
LIGHT_COL = np.array([1.0, 0.96, 0.9]) * 1.9
FILL_DIR = np.array([-0.6, 0.5, 0.6]); FILL_DIR /= np.linalg.norm(FILL_DIR)
FILL_COL = np.array([0.55, 0.65, 0.85]) * 0.22

BMIN = np.array([b[0] for b in boxes]); BMAX = np.array([b[1] for b in boxes]); BMAT = np.array([b[2] for b in boxes])

def intersect(o, d, tmax=None):
    n = o.shape[0]
    best_t = np.full(n, np.inf); best_i = np.full(n, -1); best_kind = np.zeros(n, int)
    inv = 1.0 / np.where(np.abs(d) < 1e-9, 1e-9, d)
    for i in range(len(boxes)):
        t1 = (BMIN[i] - o) * inv; t2 = (BMAX[i] - o) * inv
        tn = np.minimum(t1, t2).max(1); tf = np.maximum(t1, t2).min(1)
        hit = (tf >= np.maximum(tn, 1e-3)) & (tn > 1e-3) & (tn < best_t)
        best_t[hit] = tn[hit]; best_i[hit] = i; best_kind[hit] = 0
    for j, (cx, cz, r, y0, y1, m) in enumerate(cyls):
        ox, oz = o[:, 0] - cx, o[:, 2] - cz
        a = d[:, 0] ** 2 + d[:, 2] ** 2 + 1e-12; b = 2 * (ox * d[:, 0] + oz * d[:, 2]); c = ox ** 2 + oz ** 2 - r * r
        disc = b * b - 4 * a * c
        ok = disc > 0
        t = np.where(ok, (-b - np.sqrt(np.maximum(disc, 0))) / (2 * a), np.inf)
        y = o[:, 1] + t * d[:, 1]
        hit = ok & (t > 1e-3) & (y > y0) & (y < y1) & (t < best_t)
        best_t[hit] = t[hit]; best_i[hit] = j; best_kind[hit] = 1
        # tapa superior (borde de la taza)
        tt = (y1 - o[:, 1]) / np.where(np.abs(d[:, 1]) < 1e-9, 1e-9, d[:, 1])
        px, pz = o[:, 0] + tt * d[:, 0] - cx, o[:, 2] + tt * d[:, 2] - cz
        hit2 = (tt > 1e-3) & (px * px + pz * pz < r * r) & (tt < best_t)
        best_t[hit2] = tt[hit2]; best_i[hit2] = j; best_kind[hit2] = 2
    return best_t, best_i, best_kind

def occluded(o, d, tmax):
    t, i, k = intersect(o, d)
    return t < tmax

def hexholes(u, v, pitch, r):
    row = np.floor(v / (pitch * 0.866))
    uu = u - (row % 2) * pitch / 2
    cu = np.round(uu / pitch) * pitch; cv = (row + 0.5) * pitch * 0.866
    return (uu - cu) ** 2 + (v - cv) ** 2 < r * r

def slots(u, v, u0, u1, v0, v1, pitch=8, w=3):
    inb = (u >= u0) & (u <= u1) & (v >= v0) & (v <= v1)
    k = (u - u0) % pitch
    return inb & (k < w)

def shade(o, d, t, i, kind):
    n = o.shape[0]
    p = o + d * t[:, None]
    col = np.zeros((n, 3)); nrm = np.zeros((n, 3)); spec = np.zeros(n); shin = np.full(n, 30.0); emis = np.zeros((n, 3))
    miss = i < 0
    # normales de cajas
    bx = (kind == 0) & ~miss
    if bx.any():
        ii = i[bx]; pp = p[bx]
        mn, mx = BMIN[ii], BMAX[ii]
        dmin = np.abs(pp - mn); dmax = np.abs(pp - mx)
        dd = np.concatenate([dmin, dmax], 1); f = dd.argmin(1)
        nn = np.zeros((len(ii), 3)); ax = f % 3; sg = np.where(f < 3, -1.0, 1.0)
        nn[np.arange(len(ii)), ax] = sg
        nrm[bx] = nn
    cy = (kind == 1) & ~miss
    if cy.any():
        for j, (cx, cz, r, y0, y1, m) in enumerate(cyls):
            s = cy & (i == j)
            v = p[s] - [cx, 0, cz]; v[:, 1] = 0
            nrm[s] = v / np.linalg.norm(v, axis=1, keepdims=True)
    nrm[(kind == 2) & ~miss] = [0, 1, 0]
    mat = np.where(miss, -1, np.where(kind == 0, BMAT[np.maximum(i, 0)], MUG))

    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    # madera
    s = mat == DESK
    plank = np.floor((z[s] + 520) / 160)
    xs_ = x[s] + plank * 377
    g = np.sin(xs_ * 0.012 + 3.0 * np.sin(z[s] * 0.035 + plank) + np.sin(xs_ * 0.003) * 2.0) * 0.5 + 0.5
    fine = np.sin(xs_ * 0.35 + 6 * np.sin(z[s] * 0.05 + plank * 1.7)) * 0.5 + 0.5
    seamw = ((z[s] + 520) % 160) < 1.2
    base = np.array([0.20, 0.12, 0.075])
    cw = base * (0.70 + 0.30 * g[:, None] + 0.10 * fine[:, None]) * (1 + 0.08 * np.sin(plank * 2.3))[:, None]
    cw[seamw] *= 0.4
    col[s] = cw; spec[s] = 0.12; shin[s] = 22
    s = mat == WALL
    glow = np.exp(-(((x[s] - 150) / 900) ** 2 + ((y[s] - 450) / 700) ** 2))
    col[s] = np.array([0.045, 0.048, 0.055]) * (0.5 + 1.1 * glow)[:, None]
    # caja de aluminio negro
    s = mat == CASE
    if s.any():
        nn = nrm[s]; c = np.tile([0.028, 0.03, 0.033], (s.sum(), 1)); sp = np.full(s.sum(), 0.45); dark = np.zeros(s.sum(), bool)
        px, py, pz = x[s], y[s], z[s]
        vtop = CY1 - py
        front = nn[:, 2] > 0.5; side = nn[:, 0] > 0.5; top = nn[:, 1] > 0.5
        u = px - CX0
        dark |= front & slots(u, vtop, 10, 140, 12, 50)
        us = CZ1 - pz
        dark |= side & slots(us, vtop, 10, DEPTH - 10, 12, 50)
        r2 = (us - RAD_U) ** 2 + (vtop - 122) ** 2
        dark |= side & (r2 < 57 ** 2) & hexholes(us, vtop, 6, 1.7)
        ring = side & (np.abs(np.sqrt(r2) - 57) < 1.0)
        c[ring] *= 1.8
        ut, wt = px - CX0, CZ1 - pz
        intop = top & (ut > 10) & (ut < 140) & (wt > 10) & (wt < DEPTH - 10)
        dark |= intop & hexholes(ut, wt, 6, 1.7)
        # juntas entre paneles (0,6 mm)
        seam = (side & ((us < 2.3) & (us > 1.7) | (us > DEPTH - 2.3) & (us < DEPTH - 1.7) | (vtop < 2.3) & (vtop > 1.7)))
        seam |= front & ((vtop < 2.3) & (vtop > 1.7))
        c[dark] = [0.006, 0.006, 0.007]; sp[dark] = 0.0
        c[seam] = [0.01, 0.01, 0.012]
        # bisel: brillo en las aristas
        ef = np.zeros(s.sum())
        for ax_i, (a, lo, hi) in enumerate([(px, CX0, CX1), (py, CY0, CY1), (pz, CZ0, CZ1)]):
            e = np.clip(1 - np.minimum(np.abs(a - lo), np.abs(a - hi)) / 1.2, 0, 1)
            e[np.abs(nn[:, ax_i]) > 0.5] = 0
            ef = np.maximum(ef, e)
        c += ef[:, None] * 0.10
        col[s] = c; spec[s] = sp + ef * 0.4; shin[s] = 55
    s = mat == RUBBER; col[s] = [0.015, 0.015, 0.016]; spec[s] = 0.02
    s = mat == MON; col[s] = [0.03, 0.032, 0.035]; spec[s] = 0.25; shin[s] = 40
    s = mat == STAND; col[s] = [0.05, 0.052, 0.056]; spec[s] = 0.5; shin[s] = 60
    s = mat == PAD; col[s] = [0.035, 0.036, 0.04]; spec[s] = 0.03
    s = mat == KEYB
    if s.any():
        kx, kz = x[s] % 19, z[s] % 19
        key = (kx > 2) & (kz > 2)
        c = np.where(key[:, None], [0.06, 0.062, 0.066], [0.02, 0.02, 0.022])
        col[s] = c; spec[s] = 0.15
    s = mat == BOOK1; col[s] = [0.25, 0.08, 0.06]; spec[s] = 0.05
    s = mat == BOOK2; col[s] = [0.55, 0.52, 0.45]; spec[s] = 0.05
    s = mat == MUG; col[s] = [0.78, 0.76, 0.72]; spec[s] = 0.6; shin[s] = 80
    s = mat == SCREEN
    if s.any():
        uu = (x[s] - MX0) / (MX1 - MX0); vv = (y[s] - MY0) / (MY1 - MY0)
        sky = np.stack([0.05 + 0.10 * vv, 0.08 + 0.14 * vv, 0.16 + 0.22 * vv], 1)
        hill = vv < 0.35 + 0.18 * np.sin(uu * 5.5 + 1.0) * np.sin(uu * 2.1)
        sky[hill] = [0.03, 0.05, 0.10]
        emis[s] = sky * 0.85; col[s] = 0.0; spec[s] = 0.3
    return p, nrm, col, spec, shin, emis, miss

def render():
    t0 = time.time()
    img = np.zeros((H_IMG, W_IMG, 3))
    aspect = W_IMG / H_IMG; th = np.tan(fov / 2)
    ys, xs = np.mgrid[0:H_IMG, 0:W_IMG]
    xs = xs.ravel(); ys = ys.ravel()
    acc = np.zeros((xs.size, 3))
    NS = 6   # muestras de luz de área
    NA = 6   # muestras de oclusión ambiental
    for sidx in range(SPP):
        jx = rng.random(xs.size) if SPP > 1 else 0.5; jy = rng.random(xs.size) if SPP > 1 else 0.5
        sx = ((xs + jx) / W_IMG * 2 - 1) * th * aspect; sy = (1 - (ys + jy) / H_IMG * 2) * th
        dirs = fwd + sx[:, None] * right + sy[:, None] * up
        dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
        CH = 120000
        for a in range(0, xs.size, CH):
            d = dirs[a:a + CH]; o = np.tile(eye, (d.shape[0], 1))
            t, i, k = intersect(o, d)
            p, n, col, spec, shin, emis, miss = shade(o, d, t, i, k)
            hitm = ~miss
            out = np.zeros((d.shape[0], 3))
            po = p + n * 0.05
            # luz de área: sombras suaves
            vis = np.zeros(d.shape[0]); ldir_mean = np.zeros((d.shape[0], 3))
            for sI in range(NS):
                q = LIGHT_C + (rng.random(3) - 0.5) * 2 * LIGHT_R * np.array([1, 0.3, 1])
                L = q - np.nan_to_num(po, posinf=0, neginf=0); dist = np.linalg.norm(L, axis=1); L /= np.maximum(dist, 1e-6)[:, None]
                occ = np.zeros(d.shape[0], bool)
                cand = hitm & ((n * L).sum(1) > 0)
                if cand.any():
                    occ[cand] = occluded(po[cand], L[cand], dist[cand])
                vis += (~occ) & cand
                ldir_mean += L
            vis /= NS; ldir_mean /= np.linalg.norm(ldir_mean, axis=1, keepdims=True)
            ndl = np.clip((n * ldir_mean).sum(1), 0, 1)
            h = ldir_mean - d; h /= np.linalg.norm(h, axis=1, keepdims=True)
            ndh = np.clip((n * h).sum(1), 0, 1)
            diff = col * (ndl * vis)[:, None] * LIGHT_COL
            spc = (spec * ndh ** shin * vis * ndl)[:, None] * LIGHT_COL
            # oclusión ambiental
            ao = np.zeros(d.shape[0])
            for aI in range(NA):
                r = rng.normal(size=(d.shape[0], 3)); r /= np.linalg.norm(r, axis=1, keepdims=True)
                r = np.where(((r * n).sum(1) < 0)[:, None], -r, r)
                occ = np.zeros(d.shape[0], bool)
                if hitm.any():
                    occ[hitm] = occluded(po[hitm], r[hitm], np.full(hitm.sum(), 160.0))
                ao += ~occ
            ao /= NA
            fill = col * (np.clip((n * FILL_DIR).sum(1), 0, 1) * 0.6 + 0.4)[:, None] * FILL_COL
            amb = col * 0.14 * ao[:, None]
            # reflejo del entorno en superficies brillantes
            rdir = d - 2 * (d * n).sum(1, keepdims=True) * n
            env = (0.04 + 0.10 * np.clip(rdir[:, 1], 0, 1))[:, None] * np.array([0.8, 0.85, 1.0])
            fres = 0.04 + 0.96 * (1 - np.clip(-(d * n).sum(1), 0, 1)) ** 5
            refl = env * (spec * (0.3 + fres))[:, None] * ao[:, None]
            out = diff + spc + fill * ao[:, None] + amb + refl + emis
            out[miss] = [0.02, 0.02, 0.025]
            acc[a:a + CH] += out
        print(f"spp {sidx + 1}/{SPP} {time.time() - t0:.0f}s", flush=True)
    img = (acc / SPP).reshape(H_IMG, W_IMG, 3)
    # tono fílmico + viñeta
    img = img * 0.95
    img = (img * (2.51 * img + 0.03)) / (img * (2.43 * img + 0.59) + 0.14)
    yy, xx = np.mgrid[0:H_IMG, 0:W_IMG]
    vig = 1 - 0.35 * (((xx / W_IMG - 0.5) * 1.2) ** 2 + ((yy / H_IMG - 0.5) * 1.4) ** 2)
    img = np.clip(img * vig[:, :, None], 0, 1) ** (1 / 2.2)
    import matplotlib.pyplot as plt
    plt.imsave(OUT, img)
    print("ok", OUT, f"{time.time() - t0:.0f}s")

render()
