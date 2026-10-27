# Rule-test fixture for terraform.iam-data-read-unscoped; never executed.
resource "aws_iam_role_policy" "execution" {
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        # ok: terraform.iam-data-read-unscoped
        Action   = ["secretsmanager:GetSecretValue", "kms:Decrypt"]
        Resource = [aws_secretsmanager_secret.a.arn]
      },
      {
        Effect   = "Allow"
        # ok: terraform.iam-data-read-unscoped
        Action   = "ecr:GetAuthorizationToken"
        Resource = "*"
      },
      {
        Effect   = "Allow"
        # ruleid: terraform.iam-data-read-unscoped
        Action   = ["s3:GetObject", "s3:ListBucket"]
        Resource = "*"
      },
      {
        Effect   = "Deny"
        # ok: terraform.iam-data-read-unscoped
        Action   = "secretsmanager:GetSecretValue"
        Resource = ["*"]
      }
    ]
  })
}

data "aws_iam_policy_document" "reader" {
  statement {
    # ruleid: terraform.iam-data-read-unscoped
    actions   = ["ssm:GetParameters"]
    resources = ["*"]
  }
  statement {
    # ok: terraform.iam-data-read-unscoped
    actions   = ["ssm:GetParameters"]
    resources = [aws_ssm_parameter.p.arn]
  }
}

# A permissions boundary grants nothing: AllowAll is its ceiling, the Denies
# are the guardrail.
data "aws_iam_policy_document" "production_boundary" {
  statement {
    sid    = "AllowAll"
    effect = "Allow"
    # ok: terraform.iam-data-read-unscoped
    actions   = ["*"]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "ci_boundary" {
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      # ok: terraform.iam-data-read-unscoped
      Action   = "*"
      Resource = "*"
    }]
  })
}

# Not a boundary: still reported.
resource "aws_iam_policy" "admin" {
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      # ruleid: terraform.iam-data-read-unscoped
      Action   = "*"
      Resource = "*"
    }]
  })
}
