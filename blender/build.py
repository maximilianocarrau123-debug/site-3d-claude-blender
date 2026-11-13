"""Modela o apartamento de 42 m² a partir da planta. 1 px da planta = 1 cm.
Uso: blender -b -P build.py -- <pasta_do_projeto> [render]
"""
import bpy, bmesh, sys, os, math
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
ROOT = argv[0]
DO_RENDER = 'render' in argv
TEX = os.path.join(ROOT, 'blender', 'tex')
H = 1.5            # altura do corte das paredes (maquete aberta)
CX, CY = 546, 500  # centro da planta em px

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
col = scene.collection


def X(px): return (px - CX) / 100.0
def Y(py): return (CY - py) / 100.0


# ---------- materiais ----------
def mat(name, color=(1, 1, 1), rough=0.6, metal=0.0, tex=None, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if tex:
        t = m.node_tree.nodes.new('ShaderNodeTexImage')
        t.image = bpy.data.images.load(os.path.join(TEX, tex))
        m.node_tree.links.new(t.outputs['Color'], b.inputs['Base Color'])
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha
        m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else m.blend_method
        try: m.surface_render_method = 'BLENDED'
        except Exception: pass
    return m


def hexc(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x ** 2.2 for x in c)


M = dict(
    piso=mat('piso_espinha', rough=0.45, tex='piso_espinha.jpg'),
    porc=mat('porcelanato', rough=0.35, tex='porcelanato.jpg'),
    banho=mat('piso_banho', rough=0.3, tex='banho.jpg'),
    granito=mat('granito', rough=0.25, tex='granito.jpg'),
    madeira=mat('madeira', rough=0.5, tex='madeira_movel.jpg'),
    tapete=mat('tapete', rough=0.95, tex='tapete.jpg'),
    tapete_claro=mat('tapete_claro', hexc('#EDEAE4'), 0.95),
    parede=mat('parede', hexc('#EFEDE8'), 0.85),
    topo=mat('parede_topo', hexc('#3E3F43'), 0.8),
    laje=mat('laje', hexc('#2C2D31'), 0.9),
    branco=mat('branco', hexc('#F4F3F0'), 0.4),
    louca=mat('louca', hexc('#FBFBFA'), 0.12),
    colchao=mat('colchao', hexc('#F1EFEA'), 0.9),
    sofa=mat('sofa', hexc('#D9D6CF'), 0.9),
    manta=mat('manta', hexc('#6E7074'), 0.9),
    cinza=mat('cinza', hexc('#8A8C90'), 0.7),
    verde_alm=mat('almofada_verde', hexc('#7F8C74'), 0.9),
    areia_alm=mat('almofada_areia', hexc('#CFC6B6'), 0.9),
    preto=mat('preto', hexc('#18191B'), 0.35),
    inox=mat('inox', hexc('#C9CCD0'), 0.25, 1.0),
    vidro=mat('vidro', hexc('#CFE3EA'), 0.05, 0.0, alpha=0.13),
    folha=mat('folha', hexc('#3F7A3A'), 0.6),
    folha2=mat('folha_escura', hexc('#2C5E2E'), 0.6),
    vaso=mat('vaso', hexc('#E6E2DA'), 0.5),
    terra=mat('terra', hexc('#3A2A20'), 0.95),
    vinho=mat('vinho', hexc('#7A2A3A'), 0.5),
    tela=mat('tela', hexc('#0B0C10'), 0.1),
)

UVS = dict(piso=(1 / 0.5, 45), porc=(1 / 0.6, 0), banho=(1 / 0.6, 0), granito=(1 / 0.8, 0),
           madeira=(1 / 1.2, 0), tapete=(1 / 0.9, 0), colchao=(3, 0), sofa=(3, 0), manta=(3, 0),
           verde_alm=(4, 0), areia_alm=(4, 0))


def uv_world(obj, key):
    """UV pelo tamanho real (metros), pra textura não esticar."""
    s, rot = UVS.get(key, (1, 0))
    me = obj.data
    uv = me.uv_layers.new(name='UVMap') if not me.uv_layers else me.uv_layers[0]
    c, sn = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    mw = obj.matrix_world
    for poly in me.polygons:
        n = (mw.to_3x3() @ poly.normal).normalized()
        for li in poly.loop_indices:
            co = mw @ me.vertices[me.loops[li].vertex_index].co
            if abs(n.z) > 0.7: u, v = co.x, co.y
            elif abs(n.x) > abs(n.y): u, v = co.y, co.z
            else: u, v = co.x, co.z
            uv.data[li].uv = ((u * c - v * sn) * s, (u * sn + v * c) * s)


def finish(obj, key, bevel=0.0, smooth=False):
    obj.data.materials.append(M[key])
    col.objects.link(obj)
    if bevel > 0:
        md = obj.modifiers.new('bevel', 'BEVEL')
        md.width = bevel; md.segments = 3; md.limit_method = 'ANGLE'
        smooth = True
    if smooth:
        for p in obj.data.polygons: p.use_smooth = True
    bpy.context.view_layer.update()
    uv_world(obj, key)
    return obj


def box(name, x0, y0, x1, y1, z0, z1, key, bevel=0.0):
    """Caixa a partir do retângulo em px da planta (x0,y0)-(x1,y1) e alturas em metros."""
    ax0, ax1 = sorted((X(x0), X(x1))); ay0, ay1 = sorted((Y(y0), Y(y1)))
    v = [(ax0, ay0, z0), (ax1, ay0, z0), (ax1, ay1, z0), (ax0, ay1, z0),
         (ax0, ay0, z1), (ax1, ay0, z1), (ax1, ay1, z1), (ax0, ay1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me = bpy.data.meshes.new(name); me.from_pydata(v, [], f); me.update()
    return finish(bpy.data.objects.new(name, me), key, bevel)


def cyl(name, cx, cy, r, z0, z1, key, sx=1.0, sy=1.0, seg=40, bevel=0.0):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=z1 - z0)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    o.location = (X(cx), Y(cy), (z0 + z1) / 2); o.scale = (sx, sy, 1)
    return finish(o, key, bevel, smooth=True)


def blob(name, cx, cy, z, rx, ry, rz, key, rotz=0.0, tilt=0.0):
    """Elipsoide (almofada, folhagem, cuba)."""
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=14, radius=1)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    o.location = (X(cx), Y(cy), z); o.scale = (rx, ry, rz); o.rotation_euler = (tilt, 0, rotz)
    return finish(o, key, smooth=True)


def wall(name, x0, y0, x1, y1, z0=0.0, z1=None):
    z1 = H if z1 is None else z1
    box(name, x0, y0, x1, y1, z0, z1, 'parede')
    if z1 >= H - 1e-6:
        box(name + '_topo', x0, y0, x1, y1, H, H + 0.012, 'topo')


def window(name, x0, y0, x1, y1, sill=0.95):
    """Trecho de parede com janela: peitoril + vidro até o corte."""
    box(name + '_peitoril', x0, y0, x1, y1, 0, sill, 'parede')
    box(name + '_soleira', x0 - 2, y0 - 2, x1 + 2, y1 + 2, sill, sill + 0.03, 'branco')
    if abs(x1 - x0) < abs(y1 - y0):
        m = (x0 + x1) / 2; box(name + '_vidro', m - 1, y0, m + 1, y1, sill + 0.03, H, 'vidro')
    else:
        m = (y0 + y1) / 2; box(name + '_vidro', x0, m - 1, x1, m + 1, sill + 0.03, H, 'vidro')


def plant(name, cx, cy, s=1.0, pot_h=0.34):
    cyl(name + '_vaso', cx, cy, 0.14 * s, 0, pot_h, 'vaso', bevel=0.01)
    cyl(name + '_terra', cx, cy, 0.125 * s, pot_h - 0.02, pot_h + 0.004, 'terra')
    import random
    r = random.Random(sum(map(ord, name)))
    n = 26
    for i in range(n):
        a = i * 2.399 + r.random() * 0.4
        ring = i / n                      # 0 = centro (em pé), 1 = borda (deitada)
        tilt = 0.25 + 1.05 * ring
        ln = (0.30 + 0.16 * r.random()) * s
        d = 0.5 * ln * math.sin(tilt)
        blob(f'{name}_folha{i}', cx + 100 * d * math.sin(a), cy + 100 * d * math.cos(a),
             pot_h + 0.5 * ln * math.cos(tilt) + 0.02, 0.055 * s, 0.012 * s, ln * 0.5,
             'folha' if i % 3 else 'folha2', rotz=-a + math.pi, tilt=tilt)


def cushion(name, cx, cy, z, w, d, h, key, rotz=0.0, tilt=0.0):
    o = box(name, CX - 50 * w, CY - 50 * d, CX + 50 * w, CY + 50 * d, -h / 2, h / 2, key, min(w, d, h) * 0.42)
    o.location = (X(cx), Y(cy), z); o.rotation_euler = (tilt, 0, rotz)
    return o


def chair(name, x0, y0, back, key='cinza'):
    """Cadeira 40x40 cm; back = lado do encosto ('L','R','T','B')."""
    box(name + '_assento', x0, y0, x0 + 40, y0 + 40, 0.42, 0.47, key, 0.012)
    for i, (dx, dy) in enumerate(((2, 2), (35, 2), (2, 35), (35, 35))):
        box(f'{name}_pe{i}', x0 + dx, y0 + dy, x0 + dx + 3, y0 + dy + 3, 0, 0.42, 'preto')
    e = dict(L=(x0, y0, x0 + 4, y0 + 40), R=(x0 + 36, y0, x0 + 40, y0 + 40),
             T=(x0, y0, x0 + 40, y0 + 4), B=(x0, y0 + 36, x0 + 40, y0 + 40))[back]
    box(name + '_encosto', *e, 0.47, 0.88, key, 0.012)


# ---------- laje ----------
box('laje_a', 190, 163, 820, 735, -0.14, 0, 'laje')
box('laje_b', 805, 363, 903, 842, -0.14, 0, 'laje')
box('laje_c', 455, 735, 805, 842, -0.14, 0, 'laje')

# ---------- pisos ----------
box('piso_quarto1', 205, 180, 450, 405, 0, 0.012, 'piso')
box('piso_quarto2', 205, 415, 450, 720, 0, 0.012, 'piso')
box('piso_soleiras', 450, 180, 465, 720, 0, 0.012, 'piso')
box('piso_sala', 465, 310, 805, 720, 0, 0.012, 'piso')
box('piso_hall', 700, 180, 805, 310, 0, 0.012, 'piso')
box('piso_cozinha', 805, 375, 890, 640, 0, 0.012, 'piso')
box('piso_banho', 465, 180, 690, 300, 0, 0.014, 'banho')
box('piso_servico', 730, 640, 890, 832, 0, 0.016, 'porc')
box('piso_varanda', 463, 740, 730, 832, 0, 0.012, 'porc')

# ---------- paredes externas ----------
wall('p_topo_a', 190, 163, 712, 180)
box('porta_entrada', 712, 167, 792, 173, 0, H, 'madeira')
wall('p_topo_b', 792, 163, 820, 180)
wall('p_esq_a', 190, 163, 205, 195)
window('jan_quarto1', 190, 195, 205, 310)
wall('p_esq_b', 190, 310, 205, 735)
wall('p_baixo_a', 205, 720, 265, 735)
window('jan_quarto2', 265, 720, 385, 735)
wall('p_baixo_b', 385, 720, 455, 735)
wall('p_dir_a', 805, 180, 820, 190)
window('jan_hall', 805, 190, 820, 270)
wall('p_dir_b', 805, 270, 820, 363)
wall('p_degrau', 805, 363, 903, 375)
wall('p_cozinha', 890, 375, 903, 842)
wall('p_servico_fundo', 730, 832, 890, 842)
wall('p_servico_varanda', 726, 740, 733, 832)
wall('p_sala_servico', 705, 610, 730, 740)
wall('p_sala_baixo_a', 455, 720, 470, 740)
wall('p_sala_baixo_b', 655, 720, 705, 740)
box('porta_varanda_vidro', 470, 728, 655, 731, 0.02, H, 'vidro')
box('porta_varanda_trilho', 470, 724, 655, 736, 0, 0.02, 'inox')
box('porta_varanda_montante', 561, 727, 564, 732, 0.02, H, 'inox')
# guarda-corpo de vidro da varanda
box('gc_frente', 455, 834, 730, 837, 0.05, 1.1, 'vidro')
box('gc_lado', 457, 740, 460, 837, 0.05, 1.1, 'vidro')
box('gc_base_frente', 455, 832, 730, 842, 0, 0.06, 'topo')
box('gc_base_lado', 455, 740, 463, 842, 0, 0.06, 'topo')
box('gc_corrimao_f', 455, 833, 730, 838, 1.1, 1.13, 'inox')
box('gc_corrimao_l', 456, 740, 461, 838, 1.1, 1.13, 'inox')

# ---------- paredes internas ----------
wall('pi_quartos_a', 450, 180, 465, 325)
wall('pi_quartos_b', 450, 400, 465, 425)
wall('pi_quartos_c', 450, 500, 465, 720)
wall('pi_entre_quartos', 205, 405, 450, 415)
wall('pi_banho_a', 465, 300, 560, 310)
wall('pi_banho_b', 640, 300, 700, 310)
wall('pi_banho_dir', 690, 180, 700, 300)

# ---------- quarto 1 (solteiro) ----------
cyl('q1_tapete', 348, 300, 0.85, 0.012, 0.024, 'tapete_claro', seg=64)
box('q1_cama_base', 250, 183, 447, 257, 0.06, 0.30, 'madeira', 0.01)
box('q1_colchao', 252, 185, 445, 255, 0.30, 0.50, 'colchao', 0.03)
box('q1_manta', 340, 184, 446, 256, 0.47, 0.515, 'manta', 0.02)
for i, k in enumerate(('areia_alm', 'verde_alm', 'areia_alm')):
    cushion(f'q1_almofada{i}', 272 + i * 34, 198, 0.63, 0.30, 0.10, 0.28, k, tilt=-0.35)
box('q1_bancada_tampo', 205, 183, 250, 345, 0.72, 0.76, 'madeira', 0.006)
box('q1_bancada_lado_a', 205, 183, 250, 187, 0, 0.72, 'madeira')
box('q1_bancada_lado_b', 205, 341, 250, 345, 0, 0.72, 'madeira')
box('q1_gaveteiro', 207, 190, 248, 235, 0, 0.72, 'branco', 0.006)
box('q1_notebook_base', 214, 285, 240, 318, 0.76, 0.775, 'cinza')
box('q1_notebook_tela', 213, 285, 215, 318, 0.775, 0.97, 'tela')
box('q1_livros', 212, 205, 238, 228, 0.76, 0.84, 'vinho', 0.004)
chair('q1_cadeira', 256, 282, 'R')
box('q1_armario', 205, 348, 353, 405, 0, H, 'madeira')
box('q1_porta0', 208, 347.2, 255, 348.6, 0.03, H - 0.01, 'branco', 0.003)
box('q1_pux0', 250, 346.2, 252.5+0, 347.4, 0.6, 0.9, 'preto')
box('q1_porta1', 257, 347.2, 304, 348.6, 0.03, H - 0.01, 'branco', 0.003)
box('q1_pux1', 299, 346.2, 252.5+49, 347.4, 0.6, 0.9, 'preto')
box('q1_porta2', 306, 347.2, 353, 348.6, 0.03, H - 0.01, 'branco', 0.003)
box('q1_pux2', 348, 346.2, 252.5+98, 347.4, 0.6, 0.9, 'preto')
box('q1_armario_lado', 353, 348, 356, 405, 0, H, 'branco')

# ---------- quarto 2 (casal) ----------
box('q2_armario', 205, 415, 353, 470, 0, H, 'madeira')
box('q2_porta0', 208, 469.4, 255, 470.8, 0.03, H - 0.01, 'branco', 0.003)
box('q2_pux0', 250, 470.6, 252.5+0, 471.8, 0.6, 0.9, 'preto')
box('q2_porta1', 257, 469.4, 304, 470.8, 0.03, H - 0.01, 'branco', 0.003)
box('q2_pux1', 299, 470.6, 252.5+49, 471.8, 0.6, 0.9, 'preto')
box('q2_porta2', 306, 469.4, 353, 470.8, 0.03, H - 0.01, 'branco', 0.003)
box('q2_pux2', 348, 470.6, 252.5+98, 471.8, 0.6, 0.9, 'preto')
box('q2_armario_lado', 353, 415, 356, 470, 0, H, 'branco')
box('q2_tapete', 250, 482, 440, 712, 0.012, 0.024, 'tapete')
box('q2_cabeceira', 205, 500, 213, 680, 0, 1.05, 'madeira', 0.01)
box('q2_cama_base', 213, 513, 402, 667, 0.06, 0.28, 'madeira', 0.01)
box('q2_colchao', 215, 515, 400, 665, 0.28, 0.50, 'colchao', 0.035)
box('q2_edredom', 285, 512, 402, 668, 0.44, 0.535, 'colchao', 0.03)
box('q2_peseira', 332, 511, 372, 669, 0.46, 0.555, 'manta', 0.02)
for i, yy in enumerate((551, 628)):
    cushion(f'q2_travesseiro{i}', 240, yy, 0.565, 0.42, 0.66, 0.13, 'colchao')
    cushion(f'q2_almofada{i}', 262, yy, 0.69, 0.42, 0.42, 0.11, 'manta', rotz=math.pi / 2, tilt=-1.15)
cyl('q2_criado_redondo', 229, 492, 0.17, 0, 0.5, 'madeira', bevel=0.008)
cyl('q2_abajur_base', 229, 492, 0.05, 0.5, 0.72, 'preto')
cyl('q2_abajur_cupula', 229, 492, 0.1, 0.72, 0.88, 'areia_alm')
box('q2_criado', 207, 684, 249, 716, 0, 0.5, 'preto', 0.008)
box('q2_livro', 214, 690, 240, 708, 0.5, 0.53, 'areia_alm')
box('q2_tv', 446, 548, 450, 648, 0.80, 1.36, 'tela', 0.004)

# ---------- banheiro ----------
box('b_gabinete', 468, 182, 542, 236, 0.22, 0.80, 'branco', 0.006)
box('b_tampo', 466, 180, 544, 239, 0.80, 0.84, 'granito', 0.004)
blob('b_cuba', 505, 210, 0.87, 0.24, 0.17, 0.055, 'louca')
cyl('b_torneira', 505, 188, 0.012, 0.84, 1.02, 'inox')
box('b_torneira_bica', 503.5, 188, 506.5, 202, 1.0, 1.02, 'inox')
box('b_espelho', 472, 180.5, 540, 182, 1.0, H, 'vidro')
box('b_caixa_acoplada', 553, 182, 592, 201, 0.38, 0.80, 'louca', 0.012)
cyl('b_vaso', 572.5, 224, 0.2, 0, 0.40, 'louca', sx=0.85, sy=1.2, bevel=0.03)
cyl('b_tampa', 572.5, 224, 0.2, 0.40, 0.43, 'branco', sx=0.86, sy=1.21, bevel=0.01)
box('b_box_vidro', 611, 182, 613, 300, 0.02, H, 'vidro')
box('b_box_piso', 613, 180, 690, 300, 0.014, 0.02, 'porc')
cyl('b_chuveiro_haste', 652, 184, 0.012, 1.3, 1.34, 'inox')
cyl('b_chuveiro', 652, 196, 0.10, 1.30, 1.32, 'inox')
cyl('b_ralo', 652, 248, 0.05, 0.02, 0.024, 'inox')

# ---------- sala de jantar ----------
box('j_tampo', 577, 313, 660, 445, 0.72, 0.76, 'branco', 0.008)
for i, (dx, dy) in enumerate(((581, 317), (652, 317), (581, 437), (652, 437))):
    box(f'j_pe{i}', dx, dy, dx + 4, dy + 4, 0, 0.72, 'preto')
chair('j_cad1', 540, 326, 'L', 'preto'); chair('j_cad2', 540, 392, 'L', 'preto')
chair('j_cad3', 657, 326, 'R', 'preto'); chair('j_cad4', 657, 392, 'R', 'preto')
for i, (px, py) in enumerate(((597, 345), (640, 345), (597, 412), (640, 412))):
    cyl(f'j_prato{i}', px, py, 0.125, 0.76, 0.772, 'louca')
cyl('j_vaso', 618, 378, 0.045, 0.76, 0.90, 'vaso')
for i in range(5):
    blob(f'j_flor{i}', 618 + 5 * math.cos(i * 1.3), 378 + 5 * math.sin(i * 1.3), 0.95 + 0.02 * (i % 2), 0.045, 0.045, 0.045, 'vinho')

# ---------- sala de estar ----------
box('s_tapete', 500, 503, 660, 716, 0.012, 0.024, 'tapete')
box('s_sofa_base', 468, 505, 548, 702, 0.08, 0.40, 'sofa', 0.03)
box('s_sofa_encosto', 467, 505, 487, 702, 0.40, 0.80, 'sofa', 0.035)
box('s_sofa_braco_a', 467, 503, 548, 518, 0.40, 0.60, 'sofa', 0.03)
box('s_sofa_braco_b', 467, 690, 548, 704, 0.40, 0.60, 'sofa', 0.03)
box('s_sofa_assento_a', 488, 520, 547, 604, 0.40, 0.48, 'sofa', 0.03)
box('s_sofa_assento_b', 488, 606, 547, 688, 0.40, 0.48, 'sofa', 0.03)
for i, (yy, k) in enumerate(((538, 'verde_alm'), (572, 'areia_alm'), (612, 'cinza'), (650, 'verde_alm'))):
    cushion(f's_almofada{i}', 499, yy, 0.64, 0.38, 0.12, 0.36, k, rotz=math.pi / 2 + 0.08 * (i - 1.5), tilt=-0.3)
box('s_mesa_centro', 562, 640, 606, 684, 0.30, 0.34, 'madeira', 0.008)
for i, (dx, dy) in enumerate(((564, 642), (601, 642), (564, 679), (601, 679))):
    box(f's_mesa_pe{i}', dx, dy, dx + 3, dy + 3, 0, 0.30, 'preto')
cyl('s_bandeja', 584, 662, 0.11, 0.34, 0.352, 'vaso')
box('s_rack', 662, 512, 705, 716, 0.12, 0.48, 'madeira', 0.006)
box('s_rack_pes', 666, 516, 701, 712, 0, 0.12, 'preto')
box('s_painel', 701, 512, 705, 716, 0.48, H, 'madeira')
box('s_tv', 697, 566, 700.5, 690, 0.72, 1.40, 'tela', 0.004)
box('s_aparador', 706, 512, 728, 606, 0, 0.75, 'madeira', 0.006)
box('s_livros', 670, 524, 694, 548, 0.48, 0.60, 'areia_alm', 0.004)
plant('s_planta', 717, 585, 0.6, 0.20)
for o in [o for o in col.objects if o.name.startswith('s_planta')]: o.location.z += 0.75

# ---------- cozinha ----------
box('c_geladeira', 814, 385, 888, 448, 0, H, 'inox', 0.012)
box('c_geladeira_porta', 811, 387, 814, 446, 0.03, H - 0.01, 'inox', 0.004)
box('c_geladeira_puxador', 808.5, 392, 811, 394, 0.7, 1.3, 'preto')
box('c_gabinete', 830, 452, 888, 632, 0.10, 0.86, 'branco', 0.004)
box('c_rodape', 833, 452, 888, 632, 0, 0.10, 'preto')
box('c_tampo', 827, 450, 889, 634, 0.86, 0.90, 'granito', 0.004)
for i in range(3):
    box(f'c_puxador{i}', 828, 470 + i * 60, 830, 500 + i * 60, 0.74, 0.755, 'inox')
box('c_cuba', 838, 486, 880, 532, 0.895, 0.906, 'inox')
box('c_cuba_fundo', 842, 490, 876, 528, 0.900, 0.908, 'cinza')
cyl('c_torneira', 883, 509, 0.013, 0.90, 1.16, 'inox')
box('c_torneira_bica', 866, 507.5, 884, 510.5, 1.14, 1.16, 'inox')
box('c_cooktop', 834, 576, 884, 628, 0.90, 0.912, 'tela', 0.003)
for i, (px, py) in enumerate(((847, 589), (871, 589), (847, 615), (871, 615))):
    cyl(f'c_boca{i}', px, py, 0.075, 0.912, 0.926, 'preto')
    cyl(f'c_queimador{i}', px, py, 0.035, 0.926, 0.936, 'inox')
box('c_tabua', 846, 544, 874, 566, 0.90, 0.92, 'madeira', 0.004)

# ---------- área de serviço ----------
box('a_tanque_gab', 818, 648, 860, 702, 0, 0.82, 'branco', 0.006)
box('a_tanque', 816, 646, 862, 704, 0.82, 0.90, 'louca', 0.012)
box('a_tanque_cuba', 822, 654, 856, 698, 0.895, 0.905, 'cinza')
cyl('a_torneira', 839, 650, 0.012, 0.90, 1.12, 'inox')
box('a_aquecedor', 866, 644, 889, 702, 0.9, 1.45, 'branco', 0.012)
box('a_maquina', 822, 724, 888, 792, 0, 0.88, 'branco', 0.02)
cyl('a_maquina_tampa', 855, 762, 0.24, 0.88, 0.895, 'cinza')
cyl('a_maquina_visor', 855, 762, 0.18, 0.895, 0.90, 'tela')
box('a_maquina_painel', 824, 726, 886, 738, 0.88, 0.93, 'cinza', 0.006)

# ---------- varanda ----------
plant('v_planta_a', 498, 790, 1.15)
plant('v_planta_b', 703, 768, 1.0)

n_obj = len(col.objects)
print('OBJETOS:', n_obj)

# ---------- exportar ----------
os.makedirs(os.path.join(ROOT, 'site'), exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT, 'site', 'apto.glb'), export_format='GLB',
                          export_apply=True, export_yup=True, export_image_format='JPEG',
                          export_jpeg_quality=85, use_selection=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'blender', 'apto.blend'))

# ---------- render de conferência ----------
if DO_RENDER:
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = 1400, 1000
    scene.view_settings.view_transform = 'AgX'
    w = bpy.data.worlds.new('w'); scene.world = w; w.use_nodes = True
    bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.82, 0.86, 0.95, 1); bg.inputs[1].default_value = 0.9
    sun = bpy.data.objects.new('sol', bpy.data.lights.new('sol', 'SUN')); col.objects.link(sun)
    sun.data.energy = 3.2; sun.data.angle = 0.12; sun.rotation_euler = (math.radians(48), 0, math.radians(-38))
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); col.objects.link(cam); scene.camera = cam
    out = os.path.join(ROOT, 'blender', 'renders'); os.makedirs(out, exist_ok=True)
    tag = [a for a in argv if a.startswith('v')][0] if any(a.startswith('v') for a in argv) else 'v1'

    def shot(name, pos, target, lens=35, ortho=None):
        cam.location = pos
        d = Vector(target) - Vector(pos)
        cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        if ortho:
            cam.data.type = 'ORTHO'; cam.data.ortho_scale = ortho
        else:
            cam.data.type = 'PERSP'; cam.data.lens = lens
        scene.render.filepath = os.path.join(out, f'{tag}-{name}.png')
        bpy.ops.render.render(write_still=True)

    shot('topo', (0, 0, 14), (0, 0, 0), ortho=10.6)
    shot('iso', (7.5, -9.5, 9.5), (0.1, -0.2, 0.3), lens=40)
    shot('sala', (4.2, -6.2, 4.6), (0.6, -0.6, 0.4), lens=38)
print('FEITO')
