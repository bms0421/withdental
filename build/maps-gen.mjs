import fs from 'fs';
import * as d3 from 'd3-geo';
import { feature } from 'topojson-client';

const r = (n) => Math.round(n * 10) / 10;
const pathStr = (p) => p.replace(/(\d+\.\d+)/g, (m) => r(+m));

/* ---------- World map ---------- */
const land110 = JSON.parse(fs.readFileSync('node_modules/world-atlas/land-110m.json'));
const land = feature(land110, land110.objects.land);
const W = 1200, H = 600;
const proj = d3.geoNaturalEarth1().rotate([-165, 0]).scale(232).translate([W / 2 - 10, H / 2 + 40]);
const gp = d3.geoPath(proj);
// drop Antarctica by clipping latitude
const landNoAnt = { type: 'FeatureCollection', features: land.features };
const clipProj = proj.clipExtent([[0, 0], [W, H - 40]]);
const landPath = pathStr(d3.geoPath(clipProj)(landNoAnt));

const seoul = [126.98, 37.57];
const cities = [
  { n: 'Los Angeles', c: [-118.24, 34.05], dx: 10, dy: 14, a: 'start' },
  { n: 'San Francisco', c: [-122.42, 37.77], dx: 8, dy: -10, a: 'start' },
  { n: 'San Diego', c: [-117.16, 32.72], dx: 10, dy: 24, a: 'start' },
  { n: 'New York', c: [-74.0, 40.71], dx: 10, dy: 14, a: 'start' },
  { n: 'Boston', c: [-71.06, 42.36], dx: 10, dy: -8, a: 'start' },
  { n: 'Vancouver', c: [-123.12, 49.28], dx: 10, dy: -6, a: 'start' },
  { n: 'Toronto', c: [-79.38, 43.65], dx: 0, dy: 22, a: 'middle' },
  { n: 'Hawaii', c: [-157.86, 21.31], dx: 0, dy: 22, a: 'middle' },
  { n: 'Ethiopia', c: [38.74, 9.03], dx: 0, dy: 22, a: 'middle' },
  { n: 'Tokyo', c: [139.69, 35.68], dx: 10, dy: 16, a: 'start' },
  { n: 'Shanghai', c: [121.47, 31.23], dx: -10, dy: 6, a: 'end' },
  { n: 'Taiwan', c: [121.56, 25.03], dx: -10, dy: 6, a: 'end' },
  { n: 'Beijing', c: [116.4, 39.9], dx: -10, dy: -2, a: 'end' },
  { n: 'Paris', c: [2.35, 48.86], dx: 0, dy: -12, a: 'middle' },
  { n: 'Dijon', c: [5.04, 47.32], dx: 4, dy: 20, a: 'middle' },
  { n: 'Ulaanbaatar', c: [106.92, 47.92], dx: 0, dy: -12, a: 'middle' },
  { n: 'Sydney', c: [151.21, -33.87], dx: -10, dy: 6, a: 'end' },
  { n: 'Auckland', c: [174.76, -36.85], dx: 10, dy: 6, a: 'start' },
];
const S = proj(seoul);
let arcs = '', dots = '', labels = '';
for (const ct of cities) {
  const P = proj(ct.c);
  const dx = S[0] - P[0], dy = S[1] - P[1];
  const len = Math.hypot(dx, dy);
  // control point: perpendicular offset, bulge upward-ish
  let nx = -dy / len, ny = dx / len;
  if (ny > 0) { nx = -nx; ny = -ny; }
  const k = Math.min(0.32 * len, 150);
  const cx = (P[0] + S[0]) / 2 + nx * k * 0.6, cy = (P[1] + S[1]) / 2 + ny * k * 0.6;
  // stop short of Seoul so the arrowhead does not hide the dot
  const t = 1 - 9 / len;
  const ex = (1 - t) * (1 - t) * P[0] + 2 * (1 - t) * t * cx + t * t * S[0];
  const ey = (1 - t) * (1 - t) * P[1] + 2 * (1 - t) * t * cy + t * t * S[1];
  // use subdivided control point for truncated curve
  const qx = (1 - t) * P[0] + t * cx, qy = (1 - t) * P[1] + t * cy;
  arcs += `<path d="M${r(P[0])},${r(P[1])} Q${r(qx)},${r(qy)} ${r(ex)},${r(ey)}" fill="none" stroke="#26383A" stroke-width="1.4" stroke-opacity="0.75" marker-end="url(#wd-arrow)"/>`;
  dots += `<circle cx="${r(P[0])}" cy="${r(P[1])}" r="4" fill="#7A5A2E"/>`;
  labels += `<text x="${r(P[0] + ct.dx)}" y="${r(P[1] + ct.dy)}" text-anchor="${ct.a}">${ct.n}</text>`;
}
const world = `<svg viewBox="0 0 ${W} ${H - 40}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="wd-world-t" style="width: 100%; height: auto; display: block">
<title id="wd-world-t">World map: patients have travelled to WITH Dental Clinic in Seoul from Los Angeles, San Francisco, San Diego, New York, Boston, Vancouver, Toronto, Hawaii, Ethiopia, Paris, Dijon, Ulaanbaatar, Tokyo, Shanghai, Taiwan, Beijing, Sydney and Auckland since 2024.</title>
<defs><marker id="wd-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#26383A"/></marker></defs>
<path d="${landPath}" fill="#D9D5CD" stroke="#E8E6E1" stroke-width="0.6"/>
<g>${arcs}</g>
<g>${dots}</g>
<circle cx="${r(S[0])}" cy="${r(S[1])}" r="13" fill="#26383A" fill-opacity="0.15"/>
<circle cx="${r(S[0])}" cy="${r(S[1])}" r="6.5" fill="#26383A"/>
<g font-family="Noto Sans KR, sans-serif" font-size="13" fill="#42474A" stroke="#E8E6E1" stroke-width="4" stroke-linejoin="round" paint-order="stroke">${labels}</g>
<text x="${r(S[0] + 4)}" y="${r(S[1] - 18)}" text-anchor="middle" font-family="Noto Serif KR, serif" font-size="17" fill="#1C1F21" font-weight="600">Seoul</text>
</svg>`;

/* ---------- Airport map ---------- */
const land10 = JSON.parse(fs.readFileSync('node_modules/world-atlas/land-10m.json'));
const landHi = feature(land10, land10.objects.land);
const AW = 640, AH = 440;
const bbox = { type: 'Feature', geometry: { type: 'MultiPoint', coordinates: [[126.36, 37.33], [127.06, 37.72]] } };
const ap = d3.geoMercator().fitExtent([[0, 0], [AW, AH]], bbox);
const box = [[126.2, 37.2], [127.2, 37.85]];
const sel = { type: 'FeatureCollection', features: [] };
for (const f of landHi.features) for (const poly of (f.geometry.type === 'MultiPolygon' ? f.geometry.coordinates : [f.geometry.coordinates])) {
  const ring = poly[0]; if (ring.some(([x, y]) => x > box[0][0] && x < box[1][0] && y > box[0][1] && y < box[1][1])) sel.features.push({ type: 'Feature', geometry: { type: 'Polygon', coordinates: poly } });
}
let apPath = '';
const cl = (v, m) => Math.max(-8, Math.min(m + 8, v));
for (const f of sel.features) for (const ring of f.geometry.coordinates) {
  const pts = []; for (const c of ring) { const q = ap(c); const p = [r(cl(q[0], AW)), r(cl(q[1], AH))]; const last = pts[pts.length - 1]; if (!last || last[0] !== p[0] || last[1] !== p[1]) pts.push(p); }
  const keep = pts.filter((p, i) => { if (i === 0 || i === pts.length - 1) return true; const a = pts[i - 1], b = pts[i + 1]; return !((a[0] === p[0] && p[0] === b[0] && (p[0] === -8 || p[0] === AW + 8)) || (a[1] === p[1] && p[1] === b[1] && (p[1] === -8 || p[1] === AH + 8))); });
  if (keep.length > 3) apPath += 'M' + keep.map((p) => p.join(',')).join('L') + 'Z';
}
const river = [[126.55, 37.74], [126.66, 37.70], [126.74, 37.65], [126.80, 37.61], [126.85, 37.575], [126.895, 37.545], [126.93, 37.535], [126.96, 37.522], [126.99, 37.513], [127.03, 37.52], [127.06, 37.53]];
const riverD = 'M' + river.map((c) => ap(c).map(r).join(',')).join(' L');
const inc = ap([126.44, 37.46]), gim = ap([126.80, 37.558]), yeo = ap([126.925, 37.525]);
const curve = (A, B, bend) => {
  const mx = (A[0] + B[0]) / 2, my = (A[1] + B[1]) / 2;
  const dx = B[0] - A[0], dy = B[1] - A[1], l = Math.hypot(dx, dy);
  return { d: `M${r(A[0])},${r(A[1])} Q${r(mx - dy / l * bend)},${r(my + dx / l * bend)} ${r(B[0])},${r(B[1])}`, lx: mx - dy / l * bend * 0.5, ly: my + dx / l * bend * 0.5 };
};
const c1 = curve(inc, yeo, 60), c2 = curve(gim, yeo, -22);
const plane = (p) => `<g transform="translate(${r(p[0])},${r(p[1])})"><circle r="15" fill="#E8E6E1" stroke="#26383A" stroke-width="1.4"/><path d="M-1.2,-8 L1.2,-8 L1.6,-2 L8,1.6 L8,3.4 L1.6,1.4 L1.2,5.4 L3.4,7 L3.4,8.2 L0,7.2 L-3.4,8.2 L-3.4,7 L-1.2,5.4 L-1.6,1.4 L-8,3.4 L-8,1.6 L-1.6,-2 Z" fill="#26383A" transform="rotate(45)"/></g>`;
const airport = `<svg viewBox="0 0 ${AW} ${AH}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="wd-air-t" style="width: 100%; height: auto; display: block; background: #CFD6D5" overflow="hidden">
<title id="wd-air-t">Map: Yeouido is about 40 minutes from Incheon International Airport and about 15 minutes from Gimpo International Airport.</title>
<path d="${apPath}" fill="#E8E6E1" stroke="#BFC7C6" stroke-width="0.6"/>
<path d="${riverD}" fill="none" stroke="#CFD6D5" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
<text x="${r(ap([127.0, 37.6])[0])}" y="${r(ap([127.0, 37.6])[1])}" font-family="Noto Sans KR, sans-serif" font-size="13" fill="#8A9092" letter-spacing="0.2em">SEOUL</text>
<text x="${r(ap([126.62, 37.535])[0])}" y="${r(ap([126.62, 37.535])[1])}" font-family="Noto Sans KR, sans-serif" font-size="12" fill="#8A9092">Incheon</text>
<path d="${c1.d}" fill="none" stroke="#26383A" stroke-width="2" stroke-dasharray="6 5"/>
<path d="${c2.d}" fill="none" stroke="#7A5A2E" stroke-width="2.2" stroke-dasharray="6 5"/>
${plane(inc)}${plane(gim)}
<circle cx="${r(yeo[0])}" cy="${r(yeo[1])}" r="16" fill="#26383A" fill-opacity="0.18"/><circle cx="${r(yeo[0])}" cy="${r(yeo[1])}" r="8" fill="#26383A"/>
<g font-family="Noto Sans KR, sans-serif" fill="#1C1F21">
<text x="${r(inc[0])}" y="${r(inc[1] + 34)}" text-anchor="middle" font-size="14" font-weight="700">Incheon Int'l Airport</text>
<text x="${r(inc[0])}" y="${r(inc[1] + 51)}" text-anchor="middle" font-size="12" fill="#52575B">ICN</text>
<text x="${r(gim[0] - 4)}" y="${r(gim[1] - 26)}" text-anchor="middle" font-size="14" font-weight="700">Gimpo Int'l Airport</text>
<text x="${r(gim[0] - 4)}" y="${r(gim[1] - 42)}" text-anchor="middle" font-size="12" fill="#52575B">GMP</text>
<text x="${r(yeo[0] + 14)}" y="${r(yeo[1] + 30)}" text-anchor="middle" font-size="15" font-weight="700">Yeouido</text>
<text x="${r(yeo[0] + 14)}" y="${r(yeo[1] + 47)}" text-anchor="middle" font-size="12" fill="#52575B">WITH Dental Clinic</text>
</g>
<g font-family="Noto Serif KR, serif" font-weight="600">
<rect x="${r(c1.lx - 46)}" y="${r(c1.ly - 4)}" width="92" height="30" rx="15" fill="#26383A"/><text x="${r(c1.lx)}" y="${r(c1.ly + 16)}" text-anchor="middle" font-size="14" fill="#FFFFFF">≈ 40 min</text>
<rect x="${r(c2.lx - 70)}" y="${r(c2.ly + 12)}" width="84" height="30" rx="15" fill="#7A5A2E"/><text x="${r(c2.lx - 28)}" y="${r(c2.ly + 32)}" text-anchor="middle" font-size="14" fill="#FFFFFF">≈ 15 min</text>
</g>
</svg>`;

fs.writeFileSync('world.svg', world);
fs.writeFileSync('airport.svg', airport);
console.log(world.length, airport.length);
