// Rule-test fixture for javascript.express-sendfile-request-path; never executed.
const express = require("express");
const path = require("path");
const app = express();

app.get("/file", (req, res) => {
  // ruleid: javascript.express-sendfile-request-path
  res.sendFile(req.query.name);
});

app.get("/download/:f", function (req, res) {
  const target = path.join("/srv/files", req.params.f);
  // ruleid: javascript.express-sendfile-request-path
  res.download(target);
});

app.get("/safe", (req, res) => {
  // ok: javascript.express-sendfile-request-path
  res.sendFile(req.query.name, { root: "/srv/files" });
});

class StorageFileApi {
  // A storage client's own upload method named sendFile is not Express.
  async sendFile(path, body) {
    // ok: javascript.express-sendfile-request-path
    return fetch(path, { method: "POST", body });
  }
}
module.exports = { app, StorageFileApi };
