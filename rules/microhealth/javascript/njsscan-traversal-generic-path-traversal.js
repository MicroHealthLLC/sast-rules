// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
const fs = require('fs');

app.get('/read', function (req, res) {
  // ruleid: javascript.njsscan.traversal.generic-path-traversal
  fs.readFile(req.query.file, (err, data) => res.send(data));
});

ipcMain.handle('read', (file, opts) => {
  // ok: javascript.njsscan.traversal.generic-path-traversal
  return fs.readFileSync(file, 'utf8');
});
