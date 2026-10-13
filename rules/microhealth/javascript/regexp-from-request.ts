import express from 'express';
import escapeStringRegexp from 'escape-string-regexp';

const app = express();
const KEYWORDS = ['alpha', 'beta'];

app.get('/search', (req, res) => {
  // ruleid: javascript.regexp-from-request
  const re = new RegExp(req.query.q as string, 'i');
  res.json(re.test('x'));
});

app.post('/filter', (req, res) => {
  const pattern = req.body.pattern;
  // ruleid: javascript.regexp-from-request
  res.json(RegExp(`^${pattern}$`).test('x'));
});

app.get('/escaped', (req, res) => {
  // ok: javascript.regexp-from-request
  const re = new RegExp(escapeStringRegexp(req.query.q as string), 'i');
  res.json(re.test('x'));
});

function keywordMatcher(words: string[]) {
  // ok: javascript.regexp-from-request
  return new RegExp(`\\b(${words.join('|')})\\b`);
}

function globToRegExp(glob: string) {
  // ok: javascript.regexp-from-request
  return new RegExp(`^${glob.replace(/\*/g, '.*')}$`);
}

export { keywordMatcher, globToRegExp, KEYWORDS };
