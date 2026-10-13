// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
const Handlebars = require('handlebars');

app.get('/hb', function (req, res) {
  // ruleid: javascript.njsscan.xss.handlebars-safestring
  const s = new Handlebars.SafeString(req.query.html);
  res.send(s.toString());
});

const badges = labels.map((label, i) => {
  // ok: javascript.njsscan.xss.handlebars-safestring
  return new Handlebars.SafeString(label);
});
