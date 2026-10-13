# Fixture for the no-iam-creds-exposure refinement.
resource "aws_iam_role_policy" "execution" {
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        # ok: mh.opengrep.terraform.lang.security.iam.no-iam-creds-exposure.no-iam-creds-exposure
        Action   = "ecr:GetAuthorizationToken"
        Resource = "*"
      },
      {
        Effect = "Allow"
        # ruleid: mh.opengrep.terraform.lang.security.iam.no-iam-creds-exposure.no-iam-creds-exposure
        Action   = "iam:CreateAccessKey"
        Resource = "*"
      }
    ]
  })
}
