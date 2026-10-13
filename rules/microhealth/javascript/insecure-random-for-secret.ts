// Rule-test fixture: deliberate weak generators; never executed.
function makeSessionToken(): string {
  // ruleid: javascript.insecure-random-for-secret
  return Math.random().toString(36).slice(2);
}
// ruleid: javascript.insecure-random-for-secret
const resetCode = Math.floor(Math.random() * 1_000_000);
// ruleid: javascript.insecure-random-for-secret
const user = { id: 1, apiKey: Math.random().toString(16) };
// ruleid: javascript.insecure-random-for-secret
state.csrfToken = `${Date.now()}-${Math.random()}`;
// ruleid: javascript.insecure-random-for-secret
const newNonce = () =>
  Math.random().toString(36);
// ruleid: javascript.insecure-random-for-secret
const bytes = crypto.pseudoRandomBytes(16);

// ok: javascript.insecure-random-for-secret
const wait = 1000 * 2 ** 3 + Math.random() * 250;
// ok: javascript.insecure-random-for-secret
const width = `${Math.floor(Math.random() * 40) + 50}%`;
function shuffle<T>(xs: T[]): T[] {
  // ok: javascript.insecure-random-for-secret
  return xs.sort(() => Math.random() - 0.5);
}
// ok: javascript.insecure-random-for-secret
const sessionToken = crypto.randomUUID();
// ok: javascript.insecure-random-for-secret
const authorIndex = Math.floor(Math.random() * 3);
