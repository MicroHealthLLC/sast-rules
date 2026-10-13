// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
const { VM } = require('vm2');

app.get('/vm2ctx', function (req, res) {
  // ruleid: javascript.njsscan.eval.vm2-context-injection
  const vm = new VM({sandbox: req.query.ctx.data});
  res.send(vm.run('1'));
});

function make(cfg, state) {
  // ok: javascript.njsscan.eval.vm2-context-injection
  return new VM({sandbox: cfg.query.ctx.data});
}
