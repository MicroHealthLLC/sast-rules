# Fixture for the aws-ec2-security-group-allows-public-ingress refinement.
resource "aws_security_group" "alb" {
  # ok: mh.opengrep.terraform.aws.security.aws-ec2-security-group-allows-public-ingress.aws-ec2-security-group-allows-public-ingress
  ingress {
    description = "HTTPS from the internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  # ok: mh.opengrep.terraform.aws.security.aws-ec2-security-group-allows-public-ingress.aws-ec2-security-group-allows-public-ingress
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  # ruleid: mh.opengrep.terraform.aws.security.aws-ec2-security-group-allows-public-ingress.aws-ec2-security-group-allows-public-ingress
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  # ruleid: mh.opengrep.terraform.aws.security.aws-ec2-security-group-allows-public-ingress.aws-ec2-security-group-allows-public-ingress
  ingress {
    from_port   = 80
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
