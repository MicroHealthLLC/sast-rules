// Rule-test fixture for javascript.secret-compare-not-constant-time; never executed.
declare const provided: string;
declare const apiKey: string | null;
declare const raw: string;

export function check(secret: string) {
  // ruleid: javascript.secret-compare-not-constant-time
  if (provided === secret) return true;
  // ruleid: javascript.secret-compare-not-constant-time
  return apiKey !== provided;
}

export class Session {
  token = "";
  refresh(token: string) {
    // ok: javascript.secret-compare-not-constant-time
    if (token !== this.token) this.token = token;
  }
}

export function split(text: string) {
  for (const part of text.split(",")) {
    const token = part.trim();
    // ok: javascript.secret-compare-not-constant-time
    if (token === "") continue;
  }
  // ok: javascript.secret-compare-not-constant-time
  if (apiKey === null) return raw;
  return raw;
}

// A generation counter named `token`, compared with the current one.
let activeIndexToken = 0;
export function onBatch(token: number) {
  // ok: javascript.secret-compare-not-constant-time
  if (token !== activeIndexToken) return;
  activeIndexToken = token;
}

declare const inFlight: { token: string } | null;
export function reuse(token: string) {
  // ok: javascript.secret-compare-not-constant-time
  return inFlight?.token === token;
}

declare const configuredSignature: string;
export function unchanged(signature: string) {
  // ok: javascript.secret-compare-not-constant-time
  return signature === configuredSignature;
}

export function mismatch(confirm: string, password: string) {
  // ok: javascript.secret-compare-not-constant-time
  return confirm !== password;
}

declare const providedToken: string;
export function verify(token: string, req: { headers: Record<string, string> }) {
  // ruleid: javascript.secret-compare-not-constant-time
  if (providedToken === token) return true;
  // ruleid: javascript.secret-compare-not-constant-time
  return req.headers.authorization === token;
}

export function prompted(password: string, again: string, passwordRepeat: string) {
  // ok: javascript.secret-compare-not-constant-time
  if (again !== password) return false;
  // ok: javascript.secret-compare-not-constant-time
  return passwordRepeat === password;
}

declare const lastSavedSignature: { current: string };
declare const presenceSignatureRef: { current: string };
declare const prevToken: string;
declare const referenceValue: string;
declare const req: { headers: Record<string, string> };
export function fingerprints(signature: string, token: string, pass: number, password: number) {
  // ok: javascript.secret-compare-not-constant-time
  if (signature === lastSavedSignature.current) return;
  // ok: javascript.secret-compare-not-constant-time
  if (signature === presenceSignatureRef.current) return;
  // ok: javascript.secret-compare-not-constant-time
  if (token !== prevToken) return;
  // ok: javascript.secret-compare-not-constant-time
  if (pass === 0) return;
  // ok: javascript.secret-compare-not-constant-time
  if (password === 0) return;
  // ruleid: javascript.secret-compare-not-constant-time
  if (signature === req.headers["x-signature"]) return;
  // ruleid: javascript.secret-compare-not-constant-time
  if (token === referenceValue) return;
}
