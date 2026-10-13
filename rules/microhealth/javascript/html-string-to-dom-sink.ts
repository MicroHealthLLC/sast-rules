// Rule-test fixture for javascript.html-string-to-dom-sink; never executed.
declare function escapeHtml(s: string): string;
declare const vendor: { name: string; notes: string };
declare const el: HTMLElement;

export function printBrief() {
  const html = `<html><body><h1>${vendor.name}</h1><p>${vendor.notes}</p></body></html>`;
  const w = window.open("about:blank");
  // ruleid: javascript.html-string-to-dom-sink
  w!.document.write(html);
}

export function badge() {
  // ruleid: javascript.html-string-to-dom-sink
  el.innerHTML = `<span class="badge">${vendor.name}</span>`;
}

export function concatenated() {
  // ruleid: javascript.html-string-to-dom-sink
  el.insertAdjacentHTML("beforeend", "<li>" + vendor.name + "</li>");
}

export function escaped() {
  // ok: javascript.html-string-to-dom-sink
  el.innerHTML = `<span class="badge">${escapeHtml(vendor.name)}</span>`;
}

export function constant() {
  // ok: javascript.html-string-to-dom-sink
  el.innerHTML = "<span>loading…</span>";
}

export function notHtmlSink() {
  // An XML writer, a prompt, a regex: markup-looking strings never parsed as HTML.
  const xml = `<mxCell id="${vendor.name}" />`;
  const prompt = `<source n="1">${vendor.notes}</source>`;
  // ok: javascript.html-string-to-dom-sink
  return [xml, prompt];
}
