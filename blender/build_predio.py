"""Modela a torre do Elísio 660 a partir das fotos. Coordenadas = as do apartamento (x, z do site), chão em z=0 do Blender.
Uso: blender -b -P build_predio.py -- <pasta_do_projeto> [render]
"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
ROOT = argv[0]; DO_RENDER = 'render' in argv
TEX = os.path.join(ROOT, 'blender', 'tex')
FH = 2.8            # pé-direito + laje
POD = 3 * FH        # embasamento (garagens + lazer)
NF = 28             # andares da torre
UNIT_FLOOR = 18     # andar da unidade modelada (demonstração)
TW = 3.7            # largura de 1 módulo de fachada (1 janela)

bpy.ops.wm.read_factory_settings(use_empty=True)
col = bpy.context.scene.collection


# ---------- textura de fachada (1 janela por módulo, 1 andar por repetição) ----------
def facade_tex(name, wall):
    S = 512
    px = np.zeros((S, S, 4), np.float32); px[..., 3] = 1
    yy, xx = np.mgrid[0:S, 0:S]
    u = xx / S * TW; v = yy / S * FH                      # metros; v=0 é o piso do andar
    rng = np.random.default_rng(3)
    base = np.array(wall, np.float32)[None, None, :] * (1 + 0.035 * (rng.random((S, S, 1)) - 0.5))
    px[..., :3] = base
    px[(v > FH - 0.16)] *= np.array([0.93, 0.93, 0.93, 1])           # sombra da laje
    px[(np.abs(u - TW) < 0.02) | (u < 0.02)] *= np.array([0.9, 0.9, 0.9, 1])  # junta de painel
    w0, w1, s0, s1 = TW / 2 - 0.7, TW / 2 + 0.7, 1.0, 2.25
    frame = (u > w0 - 0.07) & (u < w1 + 0.07) & (v > s0 - 0.07) & (v < s1 + 0.07)
    glass = (u > w0) & (u < w1) & (v > s0) & (v < s1)
    px[frame, :3] = (0.86, 0.86, 0.85)
    g = 0.10 + 0.10 * (v - s0) / (s1 - s0)
    px[glass, 0] = g[glass] * 0.75; px[glass, 1] = g[glass] * 0.9; px[glass, 2] = g[glass] * 1.15
    mull = glass & (np.abs(u - TW / 2) < 0.025)
    px[mull, :3] = (0.8, 0.8, 0.8)
    px[(u > w0 - 0.1) & (u < w1 + 0.1) & (v > s0 - 0.13) & (v < s0 - 0.07), :3] *= 0.8   # sombra do peitoril
    img = bpy.data.images.new(name, S, S)
    img.pixels.foreach_set(px.ravel())
    p = os.path.join(TEX, name + '.png'); img.filepath_raw = p; img.file_format = 'PNG'; img.save()
    return bpy.data.images.load(p)


def mat(name, color=(1, 1, 1), rough=0.8, img=None, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1); b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if img:
        t = m.node_tree.nodes.new('ShaderNodeTexImage'); t.image = img
        m.node_tree.links.new(t.outputs['Color'], b.inputs['Base Color'])
    return m


BEGE = (0.62, 0.52, 0.42); BRANCO = (0.82, 0.80, 0.76)
M = dict(
    f_bege=mat('fachada_bege', img=facade_tex('fachada_bege', BEGE)),
    f_branca=mat('fachada_branca', img=facade_tex('fachada_branca', BRANCO)),
    bege=mat('bege', BEGE), branco=mat('branco_predio', BRANCO), cinza=mat('cinza_predio', (0.27, 0.26, 0.25)),
    escuro=mat('escuro', (0.03, 0.03, 0.035), 0.5), vidro=mat('vidro_predio', (0.25, 0.36, 0.42), 0.1, metal=0.6),
    agua=mat('agua', (0.05, 0.42, 0.55), 0.08), deck=mat('deck', (0.55, 0.50, 0.44)), verde=mat('verde', (0.10, 0.25, 0.08), 0.9),
)

acc = {k: ([], [], []) for k in M}     # verts, faces, uvs por material


def box(key, x0, x1, z0, z1, y0, y1, uo=(0.0, 0.0)):
    """x, z = planta do site (z cresce pra varanda); y = altura a partir do chão."""
    V, F, U = acc[key]
    n = len(V)
    bx0, bx1 = sorted((x0, x1)); by0, by1 = sorted((-z0, -z1))
    V += [(bx0, by0, y0), (bx1, by0, y0), (bx1, by1, y0), (bx0, by1, y0),
          (bx0, by0, y1), (bx1, by0, y1), (bx1, by1, y1), (bx0, by1, y1)]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        F.append(tuple(n + i for i in f))
        a, b, c = (Vector(V[n + f[0]]), Vector(V[n + f[1]]), Vector(V[n + f[2]]))
        nor = (b - a).cross(c - a)
        for i in f:
            p = V[n + i]
            if abs(nor.z) > max(abs(nor.x), abs(nor.y)): uv = (0.5, 0.02)          # topo/base: cai num pedaço liso
            elif abs(nor.y) > abs(nor.x): uv = ((p[0] - uo[0]) / TW, (p[2] - POD) / FH)
            else: uv = ((p[1] - uo[1]) / TW, (p[2] - POD) / FH)
            U.append(uv)


TOP = POD + NF * FH
# alas e miolo da torre (planta em "H"); a unidade fica no canto da ala direita, com a varanda na fachada z=2.45
WINGS = [(-3.7, 3.7), (-22.2, -14.8)]
for (a, b) in WINGS:
    box('f_bege', a, b, -16.05, 2.45, POD, TOP, uo=(a, -2.45))
    for xx in (a, b):                                    # pilastras brancas nos cantos
        box('branco', xx - 0.35, xx + 0.35, 2.1, 2.55, POD, TOP + 0.6)
        box('branco', xx - 0.35, xx + 0.35, -16.15, -15.7, POD, TOP + 0.6)
    for fl in (9, 19):                                   # faixas cinza
        y = POD + fl * FH
        box('cinza', a - 0.08, b + 0.08, -16.13, 2.53, y - 0.45, y + 0.05)
box('f_branca', -14.8, -3.7, -12.35, -1.25, POD, TOP, uo=(-14.8, 1.25))
box('bege', -22.2, 3.7, -16.05, 2.45, TOP, TOP + 0.35)          # platibanda
box('branco', -22.5, 4.0, -16.35, 2.75, TOP + 0.35, TOP + 0.5)
box('bege', -15.5, -3.0, -11.0, -3.0, TOP, TOP + 5.6)           # coroamento (caixa d'água / casa de máquinas)
box('branco', -15.8, -2.7, -11.3, -2.7, TOP + 5.6, TOP + 5.8)

# varandas empilhadas (a do andar da unidade fica de fora: o apartamento traz a própria)
for (a, b), flip in zip(WINGS, (1, -1)):
    c = (a + b) / 2
    x0, x1 = (c - 0.95, c + 2.75) if flip == 1 else (c - 2.75, c + 0.95)
    for fl in range(NF):
        if flip == 1 and fl == UNIT_FLOOR - 1: continue
        y = POD + fl * FH
        box('branco', x0, x1, 2.45, 3.5, y - 0.14, y)
        box('vidro', x0, x1, 3.44, 3.48, y + 0.05, y + 1.1)
        box('escuro', x0 + 0.1, x1 - 1.6, 2.44, 2.47, y + 0.05, y + 2.3)    # porta de correr da sala

# embasamento
box('branco', -34, 12, -26, 9, 0, POD - 0.2)
box('cinza', -34.1, 12.1, -26.1, 9.1, POD - 1.5, POD - 1.2)
box('deck', -34, 12, -26, 9, POD - 0.2, POD)
for i in range(7):                                       # rasgos da garagem
    box('escuro', -32 + i * 6.2, -28.5 + i * 6.2, 8.95, 9.05, 0.6, 2.4)
    box('escuro', -32 + i * 6.2, -28.5 + i * 6.2, 8.95, 9.05, 3.5, 5.2)
    box('escuro', 11.95, 12.05, -24 + i * 4.6, -21 + i * 4.6, 3.5, 5.2)
box('agua', -32, -25, -4, 6, POD, POD + 0.06)                    # piscina
box('branco', -32.4, -24.6, -4.4, 6.4, POD - 0.01, POD + 0.04)
box('verde', 6, 11, -24, 6, POD, POD + 0.5)                      # jardim do lazer
box('verde', -33, -24, -24, -8, POD, POD + 0.45)
box('branco', -33.9, 11.9, 8.7, 8.9, POD, POD + 1.1)             # guarda-corpo do embasamento
box('branco', 11.7, 11.9, -25.9, 8.9, POD, POD + 1.1)

for key, (V, F, U) in acc.items():
    if not V: continue
    me = bpy.data.meshes.new('predio_' + key); me.from_pydata(V, [], F); me.update()
    uv = me.uv_layers.new(name='UVMap')
    for i, l in enumerate(me.loops): uv.data[i].uv = U[i]
    me.materials.append(M[key])
    col.objects.link(bpy.data.objects.new('predio_' + key, me))

print('ALTURA', TOP + 5.8, 'PISO_UNIDADE', POD + (UNIT_FLOOR - 1) * FH)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT, 'site', 'predio.glb'), export_format='GLB', export_apply=True,
                          export_yup=True, export_image_format='JPEG', export_jpeg_quality=88, use_selection=True)

if DO_RENDER:
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 40; sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 1100, 1300
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (0.75, 0.82, 0.95, 1)
    sun = bpy.data.objects.new('sol', bpy.data.lights.new('sol', 'SUN')); col.objects.link(sun)
    sun.data.energy = 3.5; sun.rotation_euler = (math.radians(55), 0, math.radians(-35))
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); col.objects.link(cam); sc.camera = cam
    cam.data.lens = 40; cam.data.clip_end = 2000
    pos = Vector((95, -150, 70)); tgt = Vector((-9, 6, 44))
    cam.location = pos; cam.rotation_euler = (tgt - pos).to_track_quat('-Z', 'Y').to_euler()
    out = os.path.join(ROOT, 'blender', 'renders'); os.makedirs(out, exist_ok=True)
    sc.render.filepath = os.path.join(out, 'predio-v1.png'); bpy.ops.render.render(write_still=True)
print('FEITO')
