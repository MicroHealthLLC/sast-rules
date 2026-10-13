// License: MIT (c) MicroHealth, LLC. Test cases for the rule beside this file.
app.get('/proxy', async function (req, res) {
  // ruleid: javascript.njsscan.ssrf.node-ssrf
  const r = await fetch(req.query.url);
  res.send(await r.text());
});

app.get('/proxy2', async (request, response) => {
  // ruleid: javascript.njsscan.ssrf.node-ssrf
  const r = await fetch(request.body.target, { method: 'POST' });
  response.send(r.status);
});

// A desktop client calling its own configured endpoint.
async function tokenRequest(baseUrl, form) {
  // ok: javascript.njsscan.ssrf.node-ssrf
  const res = await fetch(`${baseUrl}/api/oauth/token`, { method: 'POST', body: form });
  return res.json();
}

async function get(url, token) {
  // ok: javascript.njsscan.ssrf.node-ssrf
  return fetch(url, { headers: { Authorization: `Bearer ${token}` } });
}
