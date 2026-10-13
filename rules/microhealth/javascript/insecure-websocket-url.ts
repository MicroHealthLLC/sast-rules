// A comment that mentions ws://example.com is not code.
// ok: javascript.insecure-websocket-url
export const note = 'see the docs';

// ruleid: javascript.insecure-websocket-url
export const feed = new WebSocket('ws://feeds.example.com/live');

export function connect(host: string) {
  // ruleid: javascript.insecure-websocket-url
  return new WebSocket(`ws://${host}/socket`);
}

// ok: javascript.insecure-websocket-url
export const secure = new WebSocket('wss://feeds.example.com/live');

// ok: javascript.insecure-websocket-url
export const local = new WebSocket('ws://localhost:5173/');

export function dev(port: number) {
  // ok: javascript.insecure-websocket-url
  return new WebSocket(`ws://127.0.0.1:${port}/`);
}
