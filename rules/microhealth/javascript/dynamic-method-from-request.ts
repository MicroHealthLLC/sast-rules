import express from 'express';

const app = express();
const actions: Record<string, (arg: string) => string> = {
  upper: (s) => s.toUpperCase(),
};

app.get('/run', (req, res) => {
  // ruleid: javascript.dynamic-method-from-request
  res.send(actions[req.query.action as string](req.query.arg as string));
});

app.get('/checked', (req, res) => {
  const name = req.query.action as string;
  if (!Object.hasOwn(actions, name)) return res.status(404).end();
  // ok: javascript.dynamic-method-from-request
  res.send(actions[name]('x'));
});

const HANDLERS: Record<string, () => void> = { help: () => {} };
export function dispatch(name: string) {
  const handler = HANDLERS[name];
  if (!handler) return;
  // ok: javascript.dynamic-method-from-request
  handler();
}

export function notify(toast: Record<string, (t: string) => void>, level: string) {
  // ok: javascript.dynamic-method-from-request
  toast[level]('done');
}

// A key typed as a union of string literals, from no request (the case the
// unsafe-dynamic-method refinement covered before this rule replaced it).
declare const client: Record<string, (...args: unknown[]) => Promise<unknown>>;
export const run = async (method: 'queryObject' | 'queryArray', args: unknown[]) => {
  // ok: javascript.dynamic-method-from-request
  return await client[method](...args);
};
