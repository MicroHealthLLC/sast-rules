// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
app.post('/loop', function (req, res) {
  var list = req.body.list;
  // ruleid: javascript.njsscan.dos.layer7-object-dos
  for (let i = 0; i < list.length; i++) {
    res.write(list[i]);
  }
});

// An IPC handler: (event, args), not (req, res).
ipcMain.handle('render', (doc, out) => {
  var list = doc.body.list;
  // ok: javascript.njsscan.dos.layer7-object-dos
  for (let i = 0; i < list.length; i++) {
    out.push(list[i]);
  }
});
