# Fixture for the hashicorp-tf-password refinement; never applied.
resource "azurerm_sql_server" "fixture" {
  # ruleid: mh.opengrep.generic.secrets.gitleaks.hashicorp-tf-password.hashicorp-tf-password
  administrator_login_password = "Q7mZr2LpX9cVb4"
}
