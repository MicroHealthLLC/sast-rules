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

http.createServer(function (req, res) {
  const id = /^\/assets\/(\d+)$/.exec(req.url);
  // ok: javascript.njsscan.redirect.express-open-redirect2
  res.writeHead(302, { location: `/download/${id[1]}` });
  // ruleid: javascript.njsscan.redirect.express-open-redirect2
  res.writeHead(302, { location: `/${req.url}` });
  // ruleid: javascript.njsscan.redirect.express-open-redirect2
  res.writeHead(302, { location: req.url });
  res.end();
});

app.get('/back', function (req, res) {
  // ok: javascript.njsscan.redirect.express-open-redirect2
  res.location('/home?from=' + req.query.from);
  // ruleid: javascript.njsscan.redirect.express-open-redirect2
  res.location('/' + req.query.from);
  res.end();
});
