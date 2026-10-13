from flask import Flask, request

app = Flask(__name__)


@app.route("/hello/<name>")
def hello(name):
    # ruleid: python.flask-returned-format-string
    return f"<h1>Hello {name}</h1>"


@app.route("/search")
def search():
    q = request.args.get("q")
    # ruleid: python.flask-returned-format-string
    return "<p>You searched for " + q + "</p>"


@app.route("/ok")
def ok():
    # ok: python.flask-returned-format-string
    return "static"
