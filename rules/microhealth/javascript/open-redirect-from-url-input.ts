// Rule-test fixture for javascript.open-redirect-from-url-input; never executed.
declare const config: { edgeFunctionUrl: string };
declare function isSafeRedirect(u: string | null): boolean;

export function afterLogin() {
  const next = new URLSearchParams(window.location.search).get("next");
  // ruleid: javascript.open-redirect-from-url-input
  window.location.href = next ?? "/";
}

export function afterLoginChecked() {
  const next = new URLSearchParams(window.location.search).get("next");
  if (!isSafeRedirect(next)) return;
  // ok: javascript.open-redirect-from-url-input
  window.location.href = next!;
}

export function afterLoginPath() {
  const tab = new URLSearchParams(location.search).get("tab");
  // ok: javascript.open-redirect-from-url-input
  window.location.href = `/settings/${tab}`;
}

export function authenticate(folder: { id: string }) {
  const authUrl = `${config.edgeFunctionUrl}/functions/v1/auth?drive_id=${folder.id}`;
  // ok: javascript.open-redirect-from-url-input
  window.location.href = authUrl;
}

export function fromHash() {
  // ruleid: javascript.open-redirect-from-url-input
  location.replace(decodeURIComponent(location.hash.slice(1)));
}
