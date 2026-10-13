const http = require('http');

function serve() {
  // ruleid: javascript.http-server-non-loopback
  const server = http.createServer((req, res) => res.end('hi'));
  server.listen(8080);
}

function serveAll() {
  // ruleid: javascript.http-server-non-loopback
  http.createServer((req, res) => res.end('hi')).listen(8080, '0.0.0.0');
}

function callback() {
  // ok: javascript.http-server-non-loopback
  const server = http.createServer();
  server.on('request', (req, res) => res.end('done'));
  server.listen(0, '127.0.0.1', () => {});
}

function callbackHost() {
  // ok: javascript.http-server-non-loopback
  const server = http.createServer();
  server.listen({ port: 0, host: 'localhost' });
}

function inline() {
  // ok: javascript.http-server-non-loopback
  http.createServer((req, res) => res.end()).listen(0, '::1');
}

module.exports = { serve, serveAll, callback, callbackHost, inline };
