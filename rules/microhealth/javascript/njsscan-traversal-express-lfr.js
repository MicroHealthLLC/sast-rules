// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
app.get('/page', function (req, res) {
  // ruleid: javascript.njsscan.traversal.express-lfr
  res.render('index', req.query);
});

views.forEach((view, res) => {
  // ok: javascript.njsscan.traversal.express-lfr
  res.render('index', view.query);
});
