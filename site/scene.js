// Palco 3D: prédio + cidade (exterior), apartamento (maquete), sol de verdade e câmera por pose.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const canvas = document.getElementById('stage');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance' });
const MOBILE = matchMedia('(max-width: 900px)').matches;
renderer.setPixelRatio(Math.min(devicePixelRatio, MOBILE ? 1.5 : 2));   // celular renderiza menos pixels
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.82;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const scene = new THREE.Scene();
scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;
scene.fog = new THREE.Fog('#070812', 260, 640);
const camera = new THREE.PerspectiveCamera(28, 1, 0.5, 2500);
const D2R = Math.PI / 180, clamp = THREE.MathUtils.clamp;

// ---------- luz ----------
const sun = new THREE.DirectionalLight('#FFE2C2', 3.4);
sun.castShadow = true; sun.shadow.mapSize.set(MOBILE ? 1024 : 2048, MOBILE ? 1024 : 2048);
sun.shadow.camera.near = 1; sun.shadow.camera.far = 520; sun.shadow.normalBias = 0.02; sun.shadow.radius = 5;
scene.add(sun, sun.target);
const hemi = new THREE.HemisphereLight('#DCE6FF', '#1A1D36', 0.28); scene.add(hemi);
const rim = new THREE.DirectionalLight('#6C8BFF', 0.5); rim.position.set(-7, 3, -6); scene.add(rim);
const under = new THREE.PointLight('#3C48E4', 26, 14, 1.8); under.position.set(0, -2.2, 0); scene.add(under);

// ---------- grupos ----------
const apto = new THREE.Group(); scene.add(apto);                 // unidade (origem do mundo = piso da unidade)
const ext = new THREE.Group(); scene.add(ext);                   // prédio + cidade
const GROUND = -56;                                              // a rua fica 56 m abaixo da unidade (18º andar)
const extMats = [];

const halo = (() => {
  const c = document.createElement('canvas'); c.width = c.height = 512; const g = c.getContext('2d');
  const r = g.createRadialGradient(256, 256, 20, 256, 256, 256);
  r.addColorStop(0, 'rgba(72,108,240,.55)'); r.addColorStop(.45, 'rgba(36,48,204,.18)'); r.addColorStop(1, 'rgba(5,5,7,0)');
  g.fillStyle = r; g.fillRect(0, 0, 512, 512);
  const m = new THREE.Mesh(new THREE.PlaneGeometry(17, 17), new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(c), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }));
  m.rotation.x = -Math.PI / 2; m.position.y = -0.9; return m;
})();
scene.add(halo);

// ---------- cidade em volta (casas baixas + algumas torres), gerada por código ----------
(function city() {
  let seed = 11; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  const ground = new THREE.Mesh(new THREE.CircleGeometry(420, 64), new THREE.MeshStandardMaterial({ color: '#77736D', roughness: 1 }));
  ground.rotation.x = -Math.PI / 2; ground.position.y = GROUND; ground.receiveShadow = true; ext.add(ground); extMats.push(ground.material);
  const N = MOBILE ? 320 : 620, geo = new THREE.BoxGeometry(1, 1, 1); geo.translate(0, 0.5, 0);
  const mat = new THREE.MeshStandardMaterial({ roughness: 0.9 }); extMats.push(mat);
  const inst = new THREE.InstancedMesh(geo, mat, N); inst.castShadow = true; inst.receiveShadow = true; inst.userData.caster = true;
  const pal = ['#E9E4DA', '#D9CDBB', '#C9B79E', '#B5694A', '#A8573D', '#EFEDE8', '#9C9A96', '#D8C9A6', '#C4A383'];
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), col = new THREE.Color(); let i = 0, guard = 0;
  while (i < N && guard++ < 9000) {
    const a = rnd() * Math.PI * 2, r = 34 + Math.pow(rnd(), 0.75) * 205;
    const x = -11 + Math.cos(a) * r, z = -8 + Math.sin(a) * r;
    if (x > -44 && x < 22 && z > -36 && z < 19) continue;                       // terreno do prédio
    if (r > 80 && (Math.cos(a) * 0.6 + Math.sin(a) * 0.8) > 0.35) continue;        // limpa a frente da câmera do hero
    const tower = rnd() < 0.035 && r > 70;
    const w = tower ? 14 + rnd() * 10 : 7 + rnd() * 9, d = tower ? 14 + rnd() * 8 : 7 + rnd() * 10;
    const h = tower ? 28 + rnd() * 40 : 3.5 + rnd() * rnd() * 11;
    q.setFromAxisAngle(THREE.Object3D.DEFAULT_UP, (Math.round(rnd() * 3) * 90 + (rnd() - 0.5) * 16) * D2R);
    m4.compose(new THREE.Vector3(x, GROUND, z), q, new THREE.Vector3(w, h, d)); inst.setMatrixAt(i, m4);
    inst.setColorAt(i, col.set(tower ? '#E6E3DC' : pal[Math.floor(rnd() * pal.length)])); i++;
  }
  inst.count = i; ext.add(inst);
})();

// moldura que marca a unidade na fachada
const frameMat = new THREE.MeshBasicMaterial({ color: '#8AA2FF', transparent: true, fog: false });
const unitFrame = new THREE.Group();
[[0, 2.85, 7.9, 0.14], [0, -0.2, 7.9, 0.14], [-3.9, 1.33, 0.14, 3.2], [3.9, 1.33, 0.14, 3.2]].forEach(([x, y, w, h]) => {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, 0.1), frameMat); m.position.set(x, y, 3.62); unitFrame.add(m);
});
ext.add(unitFrame);
const pin = document.getElementById('pin'), pinV = new THREE.Vector3();

// ---------- sol de verdade (latitude de São Paulo) ----------
const LAT = -23.5;
export const SEASONS = { verao: -23.44, outono: 0, inverno: 23.44, primavera: 0 };
export const sunState = { hour: 15.5, season: 'outono', facing: 0 };      // facing = pra onde a varanda aponta (0 N, 90 L, 180 S, 270 O)

export function solar(hour, dec) {          // altura e azimute (graus; azimute a partir do norte, sentido horário)
  const la = LAT * D2R, de = dec * D2R, H = (hour - 12) * 15 * D2R;
  const sinAlt = Math.sin(la) * Math.sin(de) + Math.cos(la) * Math.cos(de) * Math.cos(H);
  const alt = Math.asin(clamp(sinAlt, -1, 1));
  let az = Math.acos(clamp((Math.sin(de) - sinAlt * Math.sin(la)) / (Math.cos(alt) * Math.cos(la) || 1e-6), -1, 1));
  if (H > 0) az = Math.PI * 2 - az;
  return { alt: alt / D2R, az: az / D2R };
}
function sunDir(hour, dec, facing, out = new THREE.Vector3()) {
  const { alt, az } = solar(hour, dec), a = alt * D2R, d = (az - facing) * D2R;
  return out.set(-Math.sin(d) * Math.cos(a), Math.sin(a), Math.cos(d) * Math.cos(a));
}
export function sunStats(season = sunState.season, facing = sunState.facing) {
  const dec = SEASONS[season]; let rise = null, set = null, direct = 0; const step = 1 / 12;
  for (let t = 0; t < 24; t += step) {
    const s = solar(t, dec);
    if (s.alt > 0) {
      if (rise === null) rise = t; set = t + step;
      const rel = ((s.az - facing + 540) % 360) - 180;
      if (Math.abs(rel) < 80 && s.alt > 2) direct += step;         // sol de frente pra fachada da varanda
    }
  }
  const s = solar(sunState.hour, dec), rel = ((s.az - facing + 540) % 360) - 180;
  return { rise, set, direct, alt: s.alt, az: s.az, onBalcony: s.alt > 2 && Math.abs(rel) < 80, night: s.alt <= 0 };
}

// arco do sol + bússola (aparecem na seção do sol)
const arc = new THREE.Group(); scene.add(arc);
const R = 11;
const arcMat = new THREE.LineBasicMaterial({ color: '#FFD9A0', transparent: true, fog: false });
const arcLine = new THREE.Line(new THREE.BufferGeometry(), arcMat); arc.add(arcLine);
const ringMat = new THREE.LineBasicMaterial({ color: '#486CF0', transparent: true, fog: false });
arc.add(new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(Array.from({ length: 96 }, (_, i) => new THREE.Vector3(Math.cos(i / 96 * 6.2832) * R, -0.16, Math.sin(i / 96 * 6.2832) * R))), ringMat));
const ballMat = new THREE.MeshBasicMaterial({ color: '#FFE7B8', transparent: true, fog: false });
const ball = new THREE.Mesh(new THREE.SphereGeometry(0.34, 24, 16), ballMat); arc.add(ball);
const glowTex = (() => { const c = document.createElement('canvas'); c.width = c.height = 128; const g = c.getContext('2d'); const r = g.createRadialGradient(64, 64, 2, 64, 64, 64); r.addColorStop(0, 'rgba(255,225,170,1)'); r.addColorStop(.3, 'rgba(255,190,110,.45)'); r.addColorStop(1, 'rgba(255,170,80,0)'); g.fillStyle = r; g.fillRect(0, 0, 128, 128); return new THREE.CanvasTexture(c); })();
const glowMat = new THREE.SpriteMaterial({ map: glowTex, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, fog: false });
const glow = new THREE.Sprite(glowMat); glow.scale.setScalar(4.2); arc.add(glow);
const letters = ['N', 'L', 'S', 'O'].map((ch, i) => {
  const c = document.createElement('canvas'); c.width = c.height = 128; const g = c.getContext('2d');
  g.font = '500 76px "Geist Mono", ui-monospace, monospace'; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.fillStyle = ch === 'N' ? '#CCD8FC' : '#6B6F8E'; g.fillText(ch, 64, 70);
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(c), transparent: true, depthWrite: false, fog: false }));
  s.scale.setScalar(1.25); s.userData.bearing = i * 90; arc.add(s); return s;
});
const arcMats = [arcMat, ringMat, ballMat, glowMat, ...letters.map(l => l.material)];

const warm = new THREE.Color('#FF8A45'), noon = new THREE.Color('#FFF3E2'), tmpC = new THREE.Color();
export function applySun() {
  const dec = SEASONS[sunState.season], f = sunState.facing;
  const dir = sunDir(sunState.hour, dec, f), alt = solar(sunState.hour, dec).alt, day = clamp(alt / 12, 0, 1);
  sun.position.copy(dir).multiplyScalar(240); sun.target.position.set(0, 0, 0);
  sun.intensity = 3.7 * Math.pow(day, 0.7) * (0.55 + 0.45 * clamp(alt / 50, 0, 1));
  sun.color.copy(tmpC.copy(warm).lerp(noon, clamp(alt / 32, 0, 1)));
  hemi.intensity = 0.07 + 0.25 * day; scene.environmentIntensity = 0.06 + 0.26 * day;
  ball.position.copy(dir).multiplyScalar(R); glow.position.copy(ball.position); ball.visible = glow.visible = alt > -1;
  const pts = [];
  for (let t = 0; t <= 24; t += 0.2) { if (solar(t, dec).alt > 0) pts.push(sunDir(t, dec, f).multiplyScalar(R)); }
  arcLine.geometry.dispose(); arcLine.geometry = new THREE.BufferGeometry().setFromPoints(pts);
  letters.forEach(l => { const d = (l.userData.bearing - f) * D2R; l.position.set(-Math.sin(d) * (R + 1.3), 0.1, Math.cos(d) * (R + 1.3)); });
}

// ---------- câmera por pose ----------
// x = direita da planta, z = lado da varanda, y = altura. ext: 1 = prédio visível, 0 = só a unidade. arc: arco do sol.
export const poses = {
  hero:     { t: [-9, -13, -7],      az: 37,  el: 13, d: 262,  x: 0.16,  y: 0, ext: 1, arc: 0 },
  unidade:  { t: [0, 1.2, 3],        az: 24,  el: 7,  d: 62,   x: -0.15, y: 0, ext: 1, arc: 0 },
  sala:     { t: [0.75, 0.3, 0.6],   az: 26,  el: 44, d: 15.5, x: 0.17,  y: 0, ext: 0, arc: 0 },
  cozinha:  { t: [2.6, 0.4, 0.6],    az: -40, el: 40, d: 13,   x: -0.17, y: 0, ext: 0, arc: 0 },
  casal:    { t: [-2.1, 0.3, 0.9],   az: 42,  el: 50, d: 13,   x: 0.17,  y: 0, ext: 0, arc: 0 },
  solteiro: { t: [-2.1, 0.3, -2.0],  az: 58,  el: 54, d: 12,   x: -0.17, y: 0, ext: 0, arc: 0 },
  banho:    { t: [0.3, 0.3, -2.5],   az: 16,  el: 58, d: 10.5, x: 0.17,  y: 0, ext: 0, arc: 0 },
  varanda:  { t: [1.2, 0.3, 2.8],    az: 22,  el: 32, d: 13.5, x: -0.17, y: 0, ext: 0, arc: 0 },
  sol:      { t: [0, 2.2, 0],        az: 32,  el: 24, d: 44,   x: 0.15,  y: 0.02, ext: 0, arc: 1 },
  planta:   { t: [0.1, 0, 0.3],      az: 0,   el: 87, d: 22,   x: 0.2,   y: 0, ext: 0, arc: 0 },
};
const F = ['az', 'el', 'ld', 'x', 'y', 'ext', 'arc'];
const mk = p => ({ t: new THREE.Vector3(...p.t), az: p.az, el: p.el, ld: Math.log(p.d), x: p.x, y: p.y, ext: p.ext, arc: p.arc });
const cur = mk(poses.hero), goal = mk(poses.hero);
export const drag = { az: 0, el: 0 };
let aspectK = 1;
export function setGoal(p) { goal.t.set(...p.t); for (const f of F) goal[f] = f === 'ld' ? Math.log(p.d) : p[f]; }

function resize() {
  const w = innerWidth, h = innerHeight;
  renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
  aspectK = w / h < 1 ? 1.75 : w / h < 1.4 ? 1.25 : 1;
}
addEventListener('resize', resize); resize();

let down = null;
canvas.addEventListener('pointerdown', e => { down = { x: e.clientX, y: e.clientY, az: drag.az, el: drag.el }; });
addEventListener('pointermove', e => {
  if (!down) return;
  drag.az = down.az - (e.clientX - down.x) * 0.25;
  drag.el = clamp(down.el + (e.clientY - down.y) * 0.12, -18, 30);
  document.body.classList.add('dragging');
});
addEventListener('pointerup', () => { down = null; document.body.classList.remove('dragging'); });

const SNAP = location.search.includes('snap');   // sem inércia, só pra conferir enquadramento
const clock = new THREE.Clock(); let visible = true, shadowSize = 0;
document.addEventListener('visibilitychange', () => { visible = !document.hidden; });
const smooth = t => t * t * (3 - 2 * t);
const casters = [];

function frame() {
  requestAnimationFrame(frame);
  if (!visible) return;
  const dt = Math.min(clock.getDelta(), 0.05), k = SNAP ? 1 : 1 - Math.pow(0.0012, dt);
  if (!down) { drag.az *= 1 - 1.6 * dt; drag.el *= 1 - 1.6 * dt; }
  cur.t.lerp(goal.t, k);
  for (const f of F) cur[f] += (goal[f] - cur[f]) * k;
  const az = (cur.az + drag.az + Math.sin(clock.elapsedTime * 0.25) * 1.6) * D2R;
  const el = clamp(cur.el + drag.el, 3, 88) * D2R, d = Math.exp(cur.ld) * aspectK;
  camera.position.set(cur.t.x + d * Math.cos(el) * Math.sin(az), cur.t.y + d * Math.sin(el), cur.t.z + d * Math.cos(el) * Math.cos(az));
  camera.lookAt(cur.t);
  const port = camera.aspect < 1;
  camera.setViewOffset(innerWidth, innerHeight, -(port ? 0 : cur.x) * innerWidth, (port ? cur.y + 0.21 : cur.y) * innerHeight, innerWidth, innerHeight);

  // o exterior some conforme o drone entra na unidade
  const e = smooth(clamp(cur.ext, 0, 1)), solid = e > 0.985;
  ext.visible = e > 0.01;
  if (ext.visible) {
    for (const m of extMats) { m.opacity = e; m.transparent = !solid; m.depthWrite = e > 0.5; }
    for (const o of casters) o.castShadow = solid;
    frameMat.opacity = e * (0.55 + 0.45 * Math.sin(clock.elapsedTime * 3));
  }
  halo.material.opacity = 1 - e; under.intensity = 26 * (1 - e); rim.intensity = 0.5 * (1 - e);
  // a sombra cobre a quadra inteira no hero e só a unidade quando a câmera está lá dentro
  const size = solid ? 150 : 7.5;
  if (size !== shadowSize) {
    shadowSize = size; const c = sun.shadow.camera; c.left = c.bottom = -size; c.right = c.top = size; c.updateProjectionMatrix();
    sun.shadow.bias = size > 50 ? -0.0025 : -0.0004;
  }
  const a = clamp(cur.arc, 0, 1); arc.visible = a > 0.01;
  if (arc.visible) for (const m of arcMats) m.opacity = a * (m === ringMat ? 0.5 : 1);
  // etiqueta da unidade na fachada
  if (pin) {
    pinV.set(0, 3.4, 3.6).project(camera);
    const show = e > 0.6 && pinV.z < 1;
    pin.style.opacity = show ? 1 : 0;
    if (show) pin.style.transform = `translate(${((pinV.x + 1) / 2 * innerWidth).toFixed(1)}px,${((1 - pinV.y) / 2 * innerHeight).toFixed(1)}px) translate(-50%,-100%)`;
  }
  renderer.render(scene, camera);
}

const loader = new GLTFLoader();
const load = url => new Promise((res, rej) => loader.load(url, g => res(g.scene), undefined, rej));
export const ready = Promise.all([load('apto.glb'), load('predio.glb')]).then(([model, predio]) => {
  const aniso = renderer.capabilities.getMaxAnisotropy();
  model.traverse(o => {
    if (!o.isMesh) return;
    if (o.material.name === 'vidro') {
      o.material = new THREE.MeshPhysicalMaterial({ color: '#DCEBF2', roughness: 0.04, transparent: true, opacity: 0.16, depthWrite: false, envMapIntensity: 1.6 });
      o.renderOrder = 2;
    } else {
      o.castShadow = true; o.receiveShadow = true;
      if (o.material.map) o.material.map.anisotropy = aniso;
    }
  });
  apto.add(model);
  predio.position.y = GROUND;
  predio.traverse(o => {
    if (!o.isMesh) return;
    o.receiveShadow = true;
    if (o.material.map) o.material.map.anisotropy = aniso;
    extMats.push(o.material);
  });
  ext.add(predio);
  ext.traverse(o => { if (o.isMesh && o.material !== frameMat && !(o.geometry && o.geometry.type === 'CircleGeometry')) casters.push(o); });
  applySun();
  document.body.classList.add('loaded');
});
frame();
