// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
function login(req, res) {
  const token = lookupToken(req.user);
  // ruleid: javascript.njsscan.crypto.node-timing-attack
  if (token === req.headers['x-token']) {
    res.send('ok');
  }
  // ruleid: javascript.njsscan.crypto.node-timing-attack
  if (password == req.body.password) {
    res.send('ok');
  }
}

function present(token, apiKey) {
  // ok: javascript.njsscan.crypto.node-timing-attack
  if (token === '') {
    return false;
  }
  // ok: javascript.njsscan.crypto.node-timing-attack
  if (apiKey === null) {
    return false;
  }
  // ok: javascript.njsscan.crypto.node-timing-attack
  if (token !== null) {
    return true;
  }
}
