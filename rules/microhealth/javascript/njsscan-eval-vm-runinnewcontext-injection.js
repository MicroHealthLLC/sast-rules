// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
const vm = require('vm');

app.get('/vmnew', function (req, res) {
  // ruleid: javascript.njsscan.eval.vm-runinnewcontext-injection
  res.send(vm.runInNewContext('a + 1', req.query.ctx.a));
});

function run(cfg, job) {
  // ok: javascript.njsscan.eval.vm-runinnewcontext-injection
  return vm.runInNewContext('a + 1', cfg.query.ctx.a);
}
