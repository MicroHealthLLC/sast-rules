// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
const express = require('express');
const app = express();

app.get('/search', function (req, res) {
  // ruleid: javascript.njsscan.dos.regex-dos
  if (/^(a+)+$/.test(req.query.q)) res.send('ok');
});

app.post('/parse', (request, response) => {
  // ruleid: javascript.njsscan.dos.regex-dos
  const input = request.body.text;
  const ok = /(x+x+)+y/.test(input);
  response.send(String(ok));
});

// A plain function of two parameters is not a request handler.
function isValidName(text, opts) {
  // ok: javascript.njsscan.dos.regex-dos
  return /^[A-Za-z0-9_-]{1,64}$/.test(text) && !opts.strict;
}

// An Electron certificate check: `request` is Chromium's, the other is a callback.
ses.setCertificateVerifyProc((request, callback) => {
  // ok: javascript.njsscan.dos.regex-dos
  if (/^(net::)?OK$/.test(request.verificationResult)) callback(0);
});

function listItem(lines, start) {
  // ok: javascript.njsscan.dos.regex-dos
  const first = lines[start];
  return BULLET.test(first);
}
