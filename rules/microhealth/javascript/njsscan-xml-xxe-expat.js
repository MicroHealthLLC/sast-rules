// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
const expat = require('node-expat');

app.get('/xml', function (req, res) {
  const parser = new expat.Parser('UTF-8');
  // ruleid: javascript.njsscan.xml.xxe-expat
  parser.parse(req.query.xml.data);
  res.send('ok');
});

function feed(chunk, opts) {
  const parser = new expat.Parser('UTF-8');
  // ok: javascript.njsscan.xml.xxe-expat
  parser.parse(chunk.query.xml.data);
}
