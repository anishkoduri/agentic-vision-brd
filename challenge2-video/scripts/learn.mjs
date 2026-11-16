import { chromium } from 'playwright';
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
const base = 'http://localhost:5180';
await p.goto(base + '/docs/visualization.html', { waitUntil: 'networkidle' });
const info = await p.evaluate(() => ({
  h: document.documentElement.scrollHeight,
  sections: [...document.querySelectorAll('section')].map((s) => { const r = s.getBoundingClientRect(); return { h2: s.querySelector('h2')?.textContent, top: Math.round(r.top + scrollY), height: Math.round(r.height), left: Math.round(r.left), width: Math.round(r.width) }; }),
  bars: [...document.querySelectorAll('svg[aria-labelledby="t4 d4"] rect title')].filter((t) => /^1[234] h/.test(t.textContent)).map((t) => t.textContent),
  herd: [...document.querySelectorAll('section')].find((s) => /Herd day/.test(s.textContent)).querySelector('table').innerText,
}));
console.log(JSON.stringify(info, null, 1));
let i = 0;
for (const y of [0, 700, 1250, 1900]) { await p.evaluate((v) => scrollTo(0, v), y); await p.waitForTimeout(300); await p.screenshot({ path: `capture/learn/viz_${i++}.png` }); }
await p.goto(base + '/challenge2-video/app/tracklets.html', { waitUntil: 'networkidle' });
console.log('tracklets h', await p.evaluate(() => document.documentElement.scrollHeight));
await p.screenshot({ path: 'capture/learn/tracklets.png' });
await b.close();
