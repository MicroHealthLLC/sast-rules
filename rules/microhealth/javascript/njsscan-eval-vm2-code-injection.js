// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
const { VM } = require('vm2');

app.get('/vm2', function (req, res) {
  const vm = new VM();
  // ruleid: javascript.njsscan.eval.vm2-code-injection
  res.send(vm.run(req.query.code.trim()));
});

function evaluate(cfg, vm) {
  // ok: javascript.njsscan.eval.vm2-code-injection
  return vm.run(cfg.query.expr.trim());
}
