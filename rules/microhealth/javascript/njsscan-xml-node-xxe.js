// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
const libxmljs = require('libxmljs');

app.post('/xml', function (req, res) {
  // ruleid: javascript.njsscan.xml.node-xxe
  const doc = libxmljs.parseXmlString(req.query.xml, { noent: true });
  res.send(doc.toString());
});

// A cloud client parsing its own provider's error body.
async function errorFrom(res, opts) {
  // ok: javascript.njsscan.xml.node-xxe
  const text = await res.text(4096);
  const root = libxmljs.parseXml(text);
  return root;
}
