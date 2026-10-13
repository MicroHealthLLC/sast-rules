// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
const expat = require('node-expat');

app.get('/xml', function (req, res) {
  // ruleid: javascript.njsscan.xml.node-entity-expansion
  const parser = new expat.Parser();
  parser.write(req.query.xml);
  res.send('ok');
});

function feed(chunk, opts) {
  // ok: javascript.njsscan.xml.node-entity-expansion
  const parser = new expat.Parser();
  parser.write(chunk.query);
}
