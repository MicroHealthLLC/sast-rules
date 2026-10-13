// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
const path = require('path');

app.get('/file', function (req, res) {
  // ruleid: javascript.njsscan.traversal.join-resolve-path-traversal
  const p = path.join(__dirname, req.query.name.trim());
  res.sendFile(p);
});

function resolveIn(cfg, root) {
  // ok: javascript.njsscan.traversal.join-resolve-path-traversal
  return path.join(root, cfg.query.name.trim());
}
