// Static file server for the demo capture: serves the pipeline folder over HTTP/1.1.
// (python -m http.server answers HTTP/1.0, which trips an undici assertion in Node's fetch.)
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const TYPES = { '.html': 'text/html; charset=utf-8', '.md': 'text/plain; charset=utf-8', '.png': 'image/png', '.jpg': 'image/jpeg', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json' };
const port = Number(process.argv[2] ?? process.env.PORT ?? 5180);

http.createServer((req, res) => {
  const rel = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  const file = path.resolve(ROOT, '.' + (rel === '/' ? '/docs/visualization.html' : rel));
  // Only docs/ and the capture page are served; nothing outside the repo folder.
  const allowed = [path.join(ROOT, 'docs'), path.join(ROOT, 'challenge2-video', 'app')];
  if (!allowed.some((d) => file.startsWith(d + path.sep)) || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
    res.writeHead(404, { 'content-type': 'text/plain' }).end('not found');
    return;
  }
  res.writeHead(200, { 'content-type': TYPES[path.extname(file)] ?? 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
}).listen(port, '127.0.0.1', () => console.log(`serving ${ROOT} on http://127.0.0.1:${port}`));
