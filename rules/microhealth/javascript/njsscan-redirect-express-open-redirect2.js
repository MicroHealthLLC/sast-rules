// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
app.get('/go', function (req, res) {
  // ruleid: javascript.njsscan.redirect.express-open-redirect2
  res.header('Location', req.query.next);
  res.end();
});

links.forEach((target, res) => {
  // ok: javascript.njsscan.redirect.express-open-redirect2
  res.header('Location', target.next);
});
