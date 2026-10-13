export function makeToken() {
  // ruleid: javascript.insecure-random-for-secret
  return Math.random().toString(36).slice(2);
}

// ruleid: javascript.insecure-random-for-secret
const sessionId = `s-${Math.random().toString(36).slice(2)}`;

export const credentials = {
  // ruleid: javascript.insecure-random-for-secret
  resetToken: Math.floor(Math.random() * 1e6).toString(),
};

// ok: javascript.insecure-random-for-secret
const searchId = `grep-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

export function jitter(ms: number) {
  // ok: javascript.insecure-random-for-secret
  return ms + Math.random() * 100;
}

// ok: javascript.insecure-random-for-secret
const greeting = ['hi', 'hello'][Math.floor(Math.random() * 2)];

export const run = {
  sessionId: 'fixed',
  // ok: javascript.insecure-random-for-secret
  runId: `db-${Math.random().toString(36).slice(2, 8)}`,
};

export { sessionId, searchId, greeting };
