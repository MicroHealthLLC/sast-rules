// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
const Handlebars = require('handlebars');

app.get('/hb', function (req, res) {
  // ruleid: javascript.njsscan.xss.handlebars-noescape
  res.send(Handlebars.compile('{{x}}', {noEscape: true})(req.query));
});

const pages = items.map((data, i) => {
  // ok: javascript.njsscan.xss.handlebars-noescape
  return Handlebars.compile('{{x}}', {noEscape: true})(data);
});
