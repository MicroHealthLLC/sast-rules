// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
const vm = require('vm');

app.get('/vmctx', function (req, res) {
  // ruleid: javascript.njsscan.eval.vm-runincontext-injection
  const context = req.query.ctx.a;
  res.send(vm.runInContext('a + 1', context));
});

function run(cfg, job) {
  // ok: javascript.njsscan.eval.vm-runincontext-injection
  const context = cfg.query.ctx.a;
  return vm.runInContext('a + 1', context);
}
