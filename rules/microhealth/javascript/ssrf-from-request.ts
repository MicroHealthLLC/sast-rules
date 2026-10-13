import express from 'express';
import axios from 'axios';
import https from 'https';

const app = express();

app.get('/proxy', async (req, res) => {
  // ruleid: javascript.ssrf-from-request
  const answer = await fetch(req.query.url as string);
  res.send(await answer.text());
});

app.post('/hook', async (req, res) => {
  const target = `${req.body.base}/status`;
  // ruleid: javascript.ssrf-from-request
  await axios.get(target);
  res.end();
});

app.get('/image', (req, res) => {
  // ruleid: javascript.ssrf-from-request
  https.get(new URL(req.query.src as string), (r) => r.pipe(res));
});

app.get('/allowed', async (req, res) => {
  const url = req.query.url as string;
  if (!isAllowedHost(url)) return res.status(400).end();
  // ok: javascript.ssrf-from-request
  const answer = await fetch(url);
  res.send(await answer.text());
});

const get = (port: number, path: string) =>
  // ok: javascript.ssrf-from-request
  fetch(`http://127.0.0.1:${port}${path}`).then((response) => response.status);

async function docs(url: string, headers: Record<string, string>) {
  // ok: javascript.ssrf-from-request
  return fetch(url, { headers });
}

declare function isAllowedHost(url: string): boolean;
export { get, docs };
