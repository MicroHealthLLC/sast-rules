// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
app.get('/eval', function (req, res) {
  // ruleid: javascript.njsscan.eval.eval-nodejs
  eval(req.query.code);
});

app.get('/timer', function (request, response) {
  // ruleid: javascript.njsscan.eval.eval-nodejs
  const code = request.query.cb;
  setTimeout(code, 10);
});

function schedule(state, opts) {
  // ok: javascript.njsscan.eval.eval-nodejs
  setTimeout(state.query.flush, opts.delay);
}
