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
