// Rule-test fixture for javascript.react-unsanitized-inner-html; never executed.
import { useMemo } from "react";
import DOMPurify from "dompurify";

declare function sanitizeSvg(s: string): string;

export function Raw({ html }: { html: string }) {
  // ruleid: javascript.react-unsanitized-inner-html
  return <div dangerouslySetInnerHTML={{ __html: html }} />;
}

export function AtTheSink({ html }: { html: string }) {
  // ok: javascript.react-unsanitized-inner-html
  return <div className="x" dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(html) }} />;
}

export function Wrapper({ svg }: { svg: string }) {
  // ok: javascript.react-unsanitized-inner-html
  return <figure role="img" dangerouslySetInnerHTML={{ __html: sanitizeSvg(svg) }} />;
}

export function Const({ svg }: { svg: string }) {
  const sanitized = sanitizeSvg(svg);
  // ok: javascript.react-unsanitized-inner-html
  return <div dangerouslySetInnerHTML={{ __html: sanitized }} />;
}

export function Conditional({ svg }: { svg: string | null }) {
  const sanitized = svg ? sanitizeSvg(svg) : null;
  if (!sanitized) return null;
  // ok: javascript.react-unsanitized-inner-html
  return <div dangerouslySetInnerHTML={{ __html: sanitized }} />;
}

export function Memo({ svg }: { svg: string }) {
  const html = useMemo(() => {
    const built = svg.trim();
    return sanitizeSvg(built);
  }, [svg]);
  // ok: javascript.react-unsanitized-inner-html
  return <div dangerouslySetInnerHTML={{ __html: html }} />;
}

export function MemoTernary({ svg }: { svg: string | null }) {
  const safe = useMemo(() => (svg ? sanitizeSvg(svg) : null), [svg]);
  // ok: javascript.react-unsanitized-inner-html
  return <div dangerouslySetInnerHTML={{ __html: safe ?? "" }} />;
}

export function OtherCall({ md }: { md: string }) {
  const html = renderMarkdown(md);
  // ruleid: javascript.react-unsanitized-inner-html
  return <div dangerouslySetInnerHTML={{ __html: html }} />;
}

export function Literal() {
  // ok: javascript.react-unsanitized-inner-html
  return <style dangerouslySetInnerHTML={{ __html: "body{margin:0}" }} />;
}

export function ChartStyle({ id, colors }: { id: string; colors: [string, string][] }) {
  const css = colors.map(([k, c]) => `  --color-${k}: ${c};`).join("\n");
  // ok: javascript.react-unsanitized-inner-html
  return <style dangerouslySetInnerHTML={{ __html: `[data-chart=${id}] {\n${css}\n}` }} />;
}

declare function renderMarkdown(s: string): string;
