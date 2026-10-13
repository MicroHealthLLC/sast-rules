declare function escapeHtml(value: string): string;
declare const DOMPurify: { sanitize(value: string): string };

export function card(title: string, body: string) {
  // ruleid: javascript.html-template-unescaped
  return `<div class="card"><h2>${title}</h2></div>`;
}

export function row(name: string) {
  // ruleid: javascript.html-template-unescaped
  return `<td>${name}</td>`;
}

export function safeCard(title: string) {
  // ok: javascript.html-template-unescaped
  return `<div class="card"><h2>${escapeHtml(title)}</h2></div>`;
}

export function preview(markup: string) {
  // ok: javascript.html-template-unescaped
  return `<section>${DOMPurify.sanitize(markup)}</section>`;
}

export function usage(keys: string[]) {
  // ok: javascript.html-template-unescaped
  return `Usage: tueridev config set <key> <value>. Keys: ${keys.join(', ')}.`;
}

export function lockName(dir: string) {
  // ok: javascript.html-template-unescaped
  return `${dir}/<chain>`;
}

export function count(items: string[]) {
  // ok: javascript.html-template-unescaped
  return `<span>${items.length}</span>`;
}

export function total(sum: string) {
  // ruleid: javascript.html-template-unescaped
  return `Total: <b>${sum}</b>`;
}
