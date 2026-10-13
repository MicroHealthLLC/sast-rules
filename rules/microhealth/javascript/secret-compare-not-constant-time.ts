import express from 'express';

const app = express();
declare const config: { apiKey: string; webhookSecret: string };
declare function hmacOf(body: unknown): string;

app.post('/hook', (req, res) => {
  const signature = hmacOf(req.body);
  // ruleid: javascript.secret-compare-not-constant-time
  if (req.headers['x-signature'] !== signature) return res.status(401).end();
  res.end();
});

app.get('/admin', (req, res) => {
  // ruleid: javascript.secret-compare-not-constant-time
  if (req.query.key === config.apiKey) res.send('ok');
});

app.get('/status', (req, res) => {
  // ok: javascript.secret-compare-not-constant-time
  if (req.query.token === undefined) return res.status(400).end();
  // ok: javascript.secret-compare-not-constant-time
  if (req.query.mode === 'full') res.send('full');
});

export function confirmPassword(password: string, again: string) {
  // ok: javascript.secret-compare-not-constant-time
  return again !== password;
}

export function sameIntegrity(digest: string, want: string) {
  // ok: javascript.secret-compare-not-constant-time
  return digest === want;
}
