"""Gera as texturas da maquete (madeira espinha de peixe, porcelanato, granito, madeira de móvel, tecido)."""
import numpy as np
from PIL import Image, ImageFilter
import os, sys

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)
S = 1024


def tile_noise(size, cells, seed):
    """Ruído suave que repete nas bordas (value noise periódico)."""
    r = np.random.default_rng(seed)
    g = r.random((cells, cells))
    xs = np.linspace(0, cells, size, endpoint=False)
    xi = xs.astype(int); xf = xs - xi
    xf = xf * xf * (3 - 2 * xf)
    x0 = xi % cells; x1 = (xi + 1) % cells
    a = g[np.ix_(x0, x0)]; b = g[np.ix_(x0, x1)]; c = g[np.ix_(x1, x0)]; d = g[np.ix_(x1, x1)]
    fy = xf[:, None]; fx = xf[None, :]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def save(arr, name):
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(os.path.join(OUT, name), quality=92)


# 1) Piso espinha de peixe (carvalho claro). 8x8 células, tábua 1x4.
n = 4; cells = 2 * n; cs = S // cells
yy, xx = np.mgrid[0:S, 0:S]
cx = xx // cs; cy = yy // cs
d = (cx - cy) % (2 * n)
horiz = d < n
idx = np.where(horiz, d, 2 * n - 1 - d)
ox = np.where(horiz, cx - idx, cx) % cells
oy = np.where(horiz, cy, cy - idx) % cells
pid = ox * cells + oy + np.where(horiz, 0, 97)
tone_tab = rng.normal(0, 1, 400)
tone = tone_tab[pid % 400]
# coordenada ao longo e através da tábua
along = np.where(horiz, xx - ox * cs, yy - oy * cs) % S
across = np.where(horiz, yy % cs, xx % cs)
g1 = tile_noise(S, 64, 1); g2 = tile_noise(S, 8, 2)
# veio: ruído esticado na direção da tábua
gh = np.repeat(tile_noise(S, 128, 3)[:, ::16], 16, axis=1)  # esticado em x
gv = gh.T
grain = np.where(horiz, gh, gv)
base = np.array([196, 163, 122], float)
v = 1 + 0.085 * tone[..., None] + 0.10 * (grain[..., None] - 0.5) + 0.05 * (g2[..., None] - 0.5)
wood = base[None, None, :] * v
wood[..., 0] += 6 * tone; wood[..., 2] -= 5 * tone
edge = (across < 2) | (across > cs - 3) | (along < 2) | (along > n * cs - 3)
wood[edge] *= 0.72
save(wood, 'piso_espinha.jpg')

# 2) Porcelanato cinza claro (1 placa 60x60)
p = np.full((S, S, 3), 205.0)
p += 10 * (tile_noise(S, 6, 5)[..., None] - 0.5) + 5 * (tile_noise(S, 40, 6)[..., None] - 0.5)
p[..., 2] += 2
m = (xx < 5) | (xx > S - 6) | (yy < 5) | (yy > S - 6)
p[m] = [150, 150, 152]
save(p, 'porcelanato.jpg')

# 3) Porcelanato do banheiro (um pouco mais frio, placa menor)
p2 = np.full((S, S, 3), 214.0)
p2 += 8 * (tile_noise(S, 5, 8)[..., None] - 0.5)
p2[..., 0] -= 4
h = S // 2
m = (xx % h < 4) | (xx % h > h - 5) | (yy % h < 4) | (yy % h > h - 5)
p2[m] = [168, 170, 174]
save(p2, 'banho.jpg')

# 4) Granito preto/cinza salpicado
sp = rng.random((S, S))
gr = np.full((S, S, 3), 58.0)
gr += 30 * (tile_noise(S, 24, 9)[..., None] - 0.5)
gr[sp > 0.93] = [150, 150, 150]
gr[sp < 0.05] = [22, 22, 24]
img = Image.fromarray(np.clip(gr, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.1))
img.save(os.path.join(OUT, 'granito.jpg'), quality=92)

# 5) Madeira de móvel (freijó/nogueira médio), veio corrido em x
g = np.repeat(tile_noise(S, 256, 11)[:, ::32], 32, axis=1)
gb = tile_noise(S, 6, 12)
wb = np.array([138, 104, 74], float)[None, None, :] * (1 + 0.34 * (g[..., None] - 0.5) + 0.14 * (gb[..., None] - 0.5))
save(wb, 'madeira_movel.jpg')

# 6) Tecido (trama fina) em cinza claro — multiplica pela cor do material
t = np.full((S, S), 200.0)
t += 14 * ((xx // 3 + yy // 3) % 2) - 7
t += 16 * (tile_noise(S, 90, 13) - 0.5)
save(np.repeat(t[..., None], 3, axis=2), 'tecido.jpg')

# 7) Tapete (pelo curto, cinza)
r = np.full((S, S), 178.0) + 26 * (rng.random((S, S)) - 0.5) + 14 * (tile_noise(S, 10, 14) - 0.5)
img = Image.fromarray(np.clip(np.repeat(r[..., None], 3, axis=2), 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
img.save(os.path.join(OUT, 'tapete.jpg'), quality=92)
print('texturas ok ->', OUT, sorted(os.listdir(OUT)))
