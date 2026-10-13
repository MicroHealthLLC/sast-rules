// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
const express = require('express');
const app = express();

app.get('/search', function (req, res) {
  // ruleid: javascript.njsscan.dos.regex-dos
  if (/^(a+)+$/.test(req.query.q)) res.send('ok');
});

app.post('/parse', (request, response) => {
  const input = request.body.text;
  // ruleid: javascript.njsscan.dos.regex-dos
  const ok = /(x+x+)+y/.test(input);
  response.send(String(ok));
});

// Unanchored, with an unbounded run, over a whole request body.
app.post('/feed', function (req, res) {
  // ruleid: javascript.njsscan.dos.regex-dos
  const isAtom = /<feed[\s>][^]*xmlns=/.test(req.body);
  res.send(String(isAtom));
});

app.get('/dyn', function (req, res) {
  const re = new RegExp(req.query.pattern);
  // ruleid: javascript.njsscan.dos.regex-dos
  res.send(String(re.exec(req.query.text)));
});

app.get('/local', function (req, res) {
  const TRIM = /\s+$/;
  // ruleid: javascript.njsscan.dos.regex-dos
  res.send(String(TRIM.test(req.query.text)));
});

app.get('/safe', function (req, res) {
  // ok: javascript.njsscan.dos.regex-dos
  const isId = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(req.params.id);
  // ok: javascript.njsscan.dos.regex-dos
  const isDate = /^\d{4}-\d{2}-\d{2}$/.test(req.query.day);
  // ok: javascript.njsscan.dos.regex-dos
  const blank = /\s/.test(req.query.ch);
  // ok: javascript.njsscan.dos.regex-dos
  const known = tesseraService.test(req.params.id);
  res.send(String(isId && isDate && blank && known));
});

// A plain function of two parameters is not a request handler.
function isValidName(text, opts) {
  // ok: javascript.njsscan.dos.regex-dos
  return /(a+)+$/.test(text) && !opts.strict;
}

// An Electron certificate check: `request` is Chromium's, the other is a callback.
ses.setCertificateVerifyProc((request, callback) => {
  // ok: javascript.njsscan.dos.regex-dos
  if (/(net::)*OK/.test(request.verificationResult)) callback(0);
});

function listItem(lines, start) {
  const first = lines[start];
  // ok: javascript.njsscan.dos.regex-dos
  return /(\s*[-*]+)+/.test(first);
}
