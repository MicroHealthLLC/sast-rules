// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
const handlebars = require('handlebars');

app.get('/tpl', function (req, res) {
  // ruleid: javascript.njsscan.eval.server-side-template-injection
  const t = handlebars.compile(req.query.template);
  res.send(t({}));
});

function build(theme, opts) {
  // ok: javascript.njsscan.eval.server-side-template-injection
  return handlebars.compile(theme.source);
}
