// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
const vm = require('vm');

app.get('/vm', function (req, res) {
  // ruleid: javascript.njsscan.eval.vm-code-injection
  res.send(vm.runInThisContext(req.query.code.trim()));
});

function run(cfg, job) {
  // ok: javascript.njsscan.eval.vm-code-injection
  return vm.runInThisContext(cfg.query.code.trim());
}
