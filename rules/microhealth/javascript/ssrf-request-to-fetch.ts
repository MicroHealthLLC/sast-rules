// Rule-test fixture for javascript.ssrf-request-to-fetch; never executed.
declare function assertPublicHttpUrl(u: string): Promise<void>;
declare const ALLOWED: Set<string>;
declare const app: any;
declare const axios: any;

async function sitemap(origin: string) {
  // ruleid: javascript.ssrf-request-to-fetch
  return await fetch(`${origin}/sitemap.xml`);
}

async function crawl(url: string) {
  const origin = new URL(url).origin;
  return sitemap(origin);
}

async function checkedSitemap(url: string) {
  await assertPublicHttpUrl(url);
  // ok: javascript.ssrf-request-to-fetch
  return await fetch(`${url}/sitemap.xml`);
}

async function signedS3(url: string, init: RequestInit) {
  // ok: javascript.ssrf-request-to-fetch
  return await fetch(url, init);
}

export async function handler(req: Request): Promise<Response> {
  const { url, page } = await req.json();
  await crawl(url);
  await checkedSitemap(url);
  // ruleid: javascript.ssrf-request-to-fetch
  await fetch(url);
  // ok: javascript.ssrf-request-to-fetch
  await fetch(`https://graph.microsoft.com/v1.0/items/${page}`);
  // ok: javascript.ssrf-request-to-fetch
  await fetch(`${Deno.env.get("BASE")}/functions/v1/x?id=${encodeURIComponent(page)}`);
  if (ALLOWED.has(url)) {
    // ok: javascript.ssrf-request-to-fetch
    await fetch(url);
  }
  await signedS3(Deno.env.get("S3") ?? "", {});
  return new Response("ok");
}

app.get("/proxy", (req: any, res: any) => {
  // ruleid: javascript.ssrf-request-to-fetch
  axios.get(req.query.target).then((r: any) => res.send(r.data));
});
