// Rule-test fixture: addresses only; nothing here connects.
// A comment that mentions ws://example.com is not a connection.
// ruleid: javascript.insecure-websocket-url
const remote = new WebSocket("ws://example.com/socket");
// ruleid: javascript.insecure-websocket-url
const built = `ws://${location.host}/realtime`;
// ruleid: javascript.insecure-websocket-url
const upper = "WS://api.example.com";
// ok: javascript.insecure-websocket-url
const secure = new WebSocket("wss://example.com/socket");
// ok: javascript.insecure-websocket-url
const local = "ws://localhost:4000";
// ok: javascript.insecure-websocket-url
const loop = "ws://127.0.0.1:9000/x";
// ok: javascript.insecure-websocket-url
const prose = "the dev server needs ws:// for HMR";
declare const serverUrl: string;
// ok: javascript.insecure-websocket-url
const isPlain = serverUrl.startsWith('ws://') || serverUrl.startsWith("wss://");
// ok: javascript.insecure-websocket-url
const swapped = serverUrl.replace(`ws://`, "wss://");
// ruleid: javascript.insecure-websocket-url
const internal = "ws://ws-server.railway.internal:8080/realtime";
