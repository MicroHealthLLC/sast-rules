// Fixture for the hashicorp-tf-password refinement; never executed.
declare const passwordResult: { code: string };
export const code =
  // ok: mh.opengrep.generic.secrets.gitleaks.hashicorp-tf-password.hashicorp-tf-password
  passwordResult.code === "weak_password" ? "weak_password" : "unavailable";
// TypeScript is excluded from this rule (generic-api-key covers it), so none of these is reported here.
// ok: mh.opengrep.generic.secrets.gitleaks.hashicorp-tf-password.hashicorp-tf-password
const ADMIN_PASSWORD = "FluentaAdmin2026";
// ok: mh.opengrep.generic.secrets.gitleaks.hashicorp-tf-password.hashicorp-tf-password
const cfg = { user_name: "bob", password: "hunter2hunter4" };
