// Fixture for the hashicorp-tf-password refinement; never executed.
declare const passwordResult: { code: string };
export const code =
  // ok: mh.opengrep.generic.secrets.gitleaks.hashicorp-tf-password.hashicorp-tf-password
  passwordResult.code === "weak_password" ? "weak_password" : "unavailable";
