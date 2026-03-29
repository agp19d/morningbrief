################################################################################
# main.tf
# Provider configuration and state backend for the AI Morning Brief.
#
# State backend:
#   Local state is used by default (suitable for solo development).
#   To enable remote S3 state (recommended for CI/CD), uncomment the
#   backend "s3" block below and create the bucket first:
#
#     aws s3api create-bucket --bucket <your-bucket> --region us-east-1
#     aws dynamodb create-table \
#       --table-name morning-brief-tf-locks \
#       --attribute-definitions AttributeName=LockID,AttributeType=S \
#       --key-schema AttributeName=LockID,KeyType=HASH \
#       --billing-mode PAY_PER_REQUEST
################################################################################

terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # ── Remote S3 state ─────────────────────────────────────────────────────
  # State is stored in S3 with server-side encryption.
  # The bucket must exist before running terraform init.
  # DynamoDB locking is optional but recommended for team/CI use:
  #
  #   aws dynamodb create-table \
  #     --table-name morning-brief-tf-locks \
  #     --attribute-definitions AttributeName=LockID,AttributeType=S \
  #     --key-schema AttributeName=LockID,KeyType=HASH \
  #     --billing-mode PAY_PER_REQUEST
  backend "s3" {
    bucket         = "morningbrief-terraform-state"
    key            = "morning-brief/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "morning-brief-tf-locks"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = "morning-brief"
      ManagedBy = "terraform"
    }
  }
}
