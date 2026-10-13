export function merge(defaults: object, text: string) {
  const options = JSON.parse(text);
  // ruleid: javascript.object-assign-parsed-json
  return Object.assign(defaults, options);
}

export function mergeInto(text: string) {
  // ruleid: javascript.object-assign-parsed-json
  return Object.assign({}, { a: 1 }, JSON.parse(text));
}

export function streamError(line: string) {
  const chunk = JSON.parse(line);
  // ok: javascript.object-assign-parsed-json
  return Object.assign(new Error(chunk.error), { ollamaStreamError: true });
}

export function picked(text: string) {
  const parsed = JSON.parse(text);
  // ok: javascript.object-assign-parsed-json
  return Object.assign({}, { name: String(parsed.name) });
}
