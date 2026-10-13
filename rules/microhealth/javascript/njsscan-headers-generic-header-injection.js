// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
app.get('/hdr', function (req, res) {
  // ruleid: javascript.njsscan.headers.generic-header-injection
  res.set('X-Name', req.query.name);
  res.send('ok');
});

// An RLE decoder copying the tail: `out.set` is TypedArray.prototype.set.
function tail(src, out) {
  const s = src.query;
  // ok: javascript.njsscan.headers.generic-header-injection
  out.set(src.query, 0);
}
