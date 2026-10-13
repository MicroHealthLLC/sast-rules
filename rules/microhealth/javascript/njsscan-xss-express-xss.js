// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
const express = require('express');
const app = express();

app.get('/hello', function (req, res) {
  // ruleid: javascript.njsscan.xss.express-xss
  res.send('<h1>' + req.query.name + '</h1>');
});

function reply(msg, res) {
  // ok: javascript.njsscan.xss.express-xss
  res.send('<h1>' + msg.name + '</h1>');
}
