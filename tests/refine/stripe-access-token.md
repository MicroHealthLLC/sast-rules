# Fixture for the stripe-access-token refinement; never executed.

Placeholders in documentation, then a synthetic key (`sk_prod_` is a prefix the rule
matches that Stripe never issues, so no real-key scanner reports this file):

<!-- ok: mh.opengrep.generic.secrets.gitleaks.stripe-access-token.stripe-access-token -->
X-API-Key: sk_live_xxxxxxxxxxxxxxxx

<!-- ok: mh.opengrep.generic.secrets.gitleaks.stripe-access-token.stripe-access-token -->
X-API-Key: sk_test_0000000000000000

<!-- ruleid: mh.opengrep.generic.secrets.gitleaks.stripe-access-token.stripe-access-token -->
X-API-Key: sk_prod_Q7mZr2LpX9cVb4Nd8TfWk3Hs
