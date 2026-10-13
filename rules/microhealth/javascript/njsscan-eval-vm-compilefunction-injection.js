// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
const vm = require('vm');

app.get('/vmfn', function (req, res) {
  // ruleid: javascript.njsscan.eval.vm-compilefunction-injection
  const fn = vm.compileFunction('return 1', [], {parsingContext: req.query.ctx.a});
  res.send(String(fn()));
});

function build(cfg, job) {
  // ok: javascript.njsscan.eval.vm-compilefunction-injection
  return vm.compileFunction('return 1', [], {parsingContext: cfg.query.ctx.a});
}
