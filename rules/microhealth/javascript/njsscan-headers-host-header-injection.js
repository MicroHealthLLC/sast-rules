// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
app.get('/reset', function (req, res) {
  // ruleid: javascript.njsscan.headers.host-header-injection
  const link = 'https://' + req.host + '/reset';
  res.send(link);
});

function linkFor(server, opts) {
  // ok: javascript.njsscan.headers.host-header-injection
  const link = 'https://' + server.host + '/reset';
  return link;
}
