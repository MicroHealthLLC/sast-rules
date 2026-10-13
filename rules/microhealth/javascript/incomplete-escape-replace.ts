export function escapeLt(text: string) {
  // ruleid: javascript.incomplete-escape-replace
  return text.replace('<', '&lt;');
}

export function escapeQuote(text: string) {
  // ruleid: javascript.incomplete-escape-replace
  return text.replace('"', '&quot;');
}

export function escapeAll(text: string) {
  // ok: javascript.incomplete-escape-replace
  return text.replace(/</g, '&lt;');
}

export function percent(part: string) {
  // ok: javascript.incomplete-escape-replace
  return Number.parseFloat(part.replace('%', ''));
}

export function cursor(marked: string) {
  // ok: javascript.incomplete-escape-replace
  return marked.replace('|', '');
}
