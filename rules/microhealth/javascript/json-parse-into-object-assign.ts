// Rule-test fixture for javascript.json-parse-into-object-assign; never executed.
declare const text: string;
declare const schema: { parse(v: unknown): Record<string, unknown> };

export function merge(defaults: Record<string, unknown>) {
  const incoming = JSON.parse(text);
  // ruleid: javascript.json-parse-into-object-assign
  return Object.assign(defaults, incoming);
}

export function intoParsed() {
  const result = JSON.parse(text);
  // ok: javascript.json-parse-into-object-assign
  Object.assign(result, { data: [], status: 200 });
  return result;
}

export function validated(defaults: Record<string, unknown>) {
  const checked = schema.parse(JSON.parse(text));
  // ok: javascript.json-parse-into-object-assign
  return Object.assign(defaults, checked);
}
