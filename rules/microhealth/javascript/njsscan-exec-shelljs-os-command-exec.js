// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
const shell = require('shelljs');

app.get('/exec', function (req, res) {
  // ruleid: javascript.njsscan.exec.shelljs-os-command-exec
  shell.exec('ls ' + req.query.dir, { silent: true });
  res.send('ok');
});

function sweep(cfg, job) {
  // ok: javascript.njsscan.exec.shelljs-os-command-exec
  shell.exec('ls ' + cfg.query.dir, { silent: true });
}
