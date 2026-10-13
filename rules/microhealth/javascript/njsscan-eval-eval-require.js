// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
app.get('/require', function (req, res) {
  // ruleid: javascript.njsscan.eval.eval-require
  const mod = require(req.query.module);
  res.send(mod.name);
});

plugins.forEach((name, i) => {
  // ok: javascript.njsscan.eval.eval-require
  require(name);
});
