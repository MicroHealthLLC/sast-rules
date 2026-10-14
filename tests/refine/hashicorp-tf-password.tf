# Fixture for the hashicorp-tf-password refinement; synthetic values, never deployed.
resource "azurerm_container_app" "api" {
  registry {
    server               = "example.azurecr.io"
    username             = "example"
    # ok: mh.opengrep.generic.secrets.gitleaks.hashicorp-tf-password.hashicorp-tf-password
    password_secret_name = "acr-password"
  }
}

resource "azurerm_mssql_server" "db" {
  # ruleid: mh.opengrep.generic.secrets.gitleaks.hashicorp-tf-password.hashicorp-tf-password
  administrator_login_password = "Sup3rS3cret99"
}

resource "azurerm_sql_server" "fixture" {
  # ruleid: mh.opengrep.generic.secrets.gitleaks.hashicorp-tf-password.hashicorp-tf-password
  administrator_login_password = "Q7mZr2LpX9cVb4"
}

locals {
  # ok: mh.opengrep.generic.secrets.gitleaks.hashicorp-tf-password.hashicorp-tf-password
  ecr_password_var = "RAILWAY_ECR_PASSWORD"
  # ok: mh.opengrep.generic.secrets.gitleaks.hashicorp-tf-password.hashicorp-tf-password
  db_password = "PROD_DB_PASSWORD"
  # ruleid: mh.opengrep.generic.secrets.gitleaks.hashicorp-tf-password.hashicorp-tf-password
  admin_password = "FluentaAdmin2026"
}
