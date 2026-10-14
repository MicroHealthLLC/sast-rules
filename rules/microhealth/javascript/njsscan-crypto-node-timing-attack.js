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

let activeIndexToken = 0;
function onBatch(token) {
  // ok: javascript.njsscan.crypto.node-timing-attack
  if (token !== activeIndexToken) {
    return;
  }
}

function signUp(password, confirmPassword) {
  // ok: javascript.njsscan.crypto.node-timing-attack
  if (password !== confirmPassword) {
    return false;
  }
}

function check(token, providedToken) {
  // ruleid: javascript.njsscan.crypto.node-timing-attack
  if (token === providedToken) {
    return true;
  }
}

function ask(password, again) {
  // ok: javascript.njsscan.crypto.node-timing-attack
  if (again !== password) {
    return false;
  }
}

async function stale(latest, token, read) {
  await read();
  // ok: javascript.njsscan.crypto.node-timing-attack
  if (latest.current !== token) {
    return;
  }
}

function presented(request, token) {
  // ruleid: javascript.njsscan.crypto.node-timing-attack
  if (request.current === token) {
    return true;
  }
}
