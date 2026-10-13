import fs from 'fs';
import path from 'path';
import express from 'express';

const app = express();
const ROOT = '/srv/files';

app.get('/file', (req, res) => {
  // ruleid: javascript.path-traversal-from-request
  fs.readFile(path.join(ROOT, req.query.name as string), (err, data) => res.send(data));
});

app.get('/download/:name', (req, res) => {
  const target = path.resolve(ROOT, req.params.name);
  // ruleid: javascript.path-traversal-from-request
  res.sendFile(target);
});

app.post('/save', async (req, res) => {
  // ruleid: javascript.path-traversal-from-request
  await fs.promises.writeFile(req.body.path, 'x');
  res.end();
});

app.get('/safe', (req, res) => {
  // ok: javascript.path-traversal-from-request
  fs.readFile(path.join(ROOT, path.basename(req.query.name as string)), () => res.end());
});

app.get('/checked', (req, res) => {
  const target = safeJoin(ROOT, req.query.name as string);
  // ok: javascript.path-traversal-from-request
  fs.readFile(target, () => res.end());
});

app.get('/guarded', (req, res) => {
  const target = path.resolve(ROOT, req.query.name as string);
  if (!isInside(ROOT, target)) return res.status(400).end();
  // ok: javascript.path-traversal-from-request
  fs.readFile(target, () => res.end());
});

function loadSetting(dataDir: string, name: string) {
  // ok: javascript.path-traversal-from-request
  return fs.readFileSync(path.join(dataDir, `${name}.json`), 'utf8');
}

function cacheFile(folder: string, id: string) {
  // ok: javascript.path-traversal-from-request
  return fs.promises.readFile(path.join(folder, `${id}.json`), 'utf8');
}

declare function isInside(root: string, target: string): boolean;
declare function safeJoin(root: string, rel: string): string;
export { loadSetting, cacheFile };
