// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
app.get('/go', function (req, res) {
  // ruleid: javascript.njsscan.redirect.express-open-redirect
  res.redirect(req.query.next);
});

links.forEach((target, res) => {
  // ok: javascript.njsscan.redirect.express-open-redirect
  res.redirect(target.next);
});
