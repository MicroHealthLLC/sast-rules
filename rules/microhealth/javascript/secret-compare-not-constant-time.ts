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
