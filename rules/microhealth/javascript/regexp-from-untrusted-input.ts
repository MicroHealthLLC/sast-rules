// Rule-test fixture for javascript.regexp-from-untrusted-input; never executed.
declare function escapeRegExp(s: string): string;
const TAGS = ["title", "link"];

Deno.serve(async (req: Request) => {
  const body = await req.json();
  // ruleid: javascript.regexp-from-untrusted-input
  const re = new RegExp(body.pattern, "i");
  // ok: javascript.regexp-from-untrusted-input
  const literal = new RegExp(escapeRegExp(body.term), "gi");
  return new Response(String(re.test("x") || literal.test("y")));
});

export function onSearch(e: { target: { value: string } }) {
  // ruleid: javascript.regexp-from-untrusted-input
  return new RegExp(`^${e.target.value}`);
}

export function onSearchEscaped(e: { target: { value: string } }) {
  const term = e.target.value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  // ok: javascript.regexp-from-untrusted-input
  return new RegExp(term, "i");
}

export function extractTag(block: string, tag: string) {
  // A helper's parameter is not user input: callers pass constant tag names.
  // ok: javascript.regexp-from-untrusted-input
  const re = new RegExp(`<${tag}[^>]*>([\\s\\S]*?)</${tag}>`, "i");
  return re.exec(block)?.[1] ?? TAGS[0];
}
