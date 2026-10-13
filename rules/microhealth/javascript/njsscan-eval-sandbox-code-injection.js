// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
const Sandbox = require('sandbox');
const s = new Sandbox();

app.get('/run', function (req, res) {
  // ruleid: javascript.njsscan.eval.sandbox-code-injection
  s.run(req.query.code.trim(), (out) => res.send(out));
});

function drive(cfg, opts) {
  // ok: javascript.njsscan.eval.sandbox-code-injection
  s.run(cfg.query.steps.join(','), () => {});
}
