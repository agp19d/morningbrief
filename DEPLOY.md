# 🧠 AI Morning Brief — AWS Lambda Deployment Guide

Daily AI & tech news, delivered to your Gmail at **6:00 AM Panama time**, fully automated.

---

## What You'll Need

- An **AWS account** (free tier works — this costs ~$0.00/month)
- Your **Anthropic API key** → https://console.anthropic.com
- A **Gmail App Password** (not your real password — see Step 1)
- **AWS CLI + SAM CLI** installed on your machine

---

## Step 1 — Create a Gmail App Password

Gmail requires a special App Password for SMTP access.

1. Go to your Google Account → **Security**
2. Enable **2-Step Verification** (required)
3. Go to **App Passwords** → https://myaccount.google.com/apppasswords
4. Choose **Mail** + **Other (Custom name)** → name it `Morning Brief`
5. Copy the **16-character password** — you'll use it below

> ⚠️ This is different from your Gmail login password. Keep it safe.

---

## Step 2 — Install AWS CLI & SAM CLI

### Windows
```powershell
# Option A — winget (Windows 10/11 built-in)
winget install Amazon.AWSCLI
winget install Amazon.SAM-CLI

# Option B — download MSI installers directly:
# AWS CLI:  https://awscli.amazonaws.com/AWSCLIV2.msi
# SAM CLI:  https://github.com/aws/aws-sam-cli/releases/latest/download/AWS_SAM_CLI_64_PY3.msi
```

### macOS
```bash
brew install awscli aws-sam-cli
```

### Both platforms — configure AWS credentials
```bash
aws configure
# Enter when prompted:
#   AWS Access Key ID
#   AWS Secret Access Key
#   Default region (e.g. us-east-1)
#   Output format: json
```

> Get your AWS Access Key from: https://console.aws.amazon.com/iam → Users → Security credentials → Create access key

---

## Step 3 — Deploy

Navigate to the project folder and run:

```bash
cd morning-brief-lambda

# Build the package
sam build

# Deploy (interactive first time — saves config for future deploys)
sam deploy --guided
```

You'll be prompted to enter:

| Parameter | Value |
|---|---|
| `AnthropicApiKey` | `sk-ant-api03-...` |
| `GmailAddress` | `you@gmail.com` |
| `GmailAppPassword` | The 16-char app password from Step 1 |
| `ToEmail` | `you@gmail.com` (or any recipient) |
| Stack name | `morning-brief` |
| AWS Region | `us-east-1` (or your preferred region) |

SAM will create the Lambda function and the EventBridge schedule automatically.

---

## Step 4 — Test It Manually

After deploying, trigger it immediately to confirm it works:

```bash
aws lambda invoke \
  --function-name ai-morning-brief \
  --payload '{}' \
  response.json

cat response.json
```

You should see:
```json
{"statusCode": 200, "body": "{\"status\": \"sent\", \"headline\": \"...\"}"}
```

And an email in your inbox within seconds. ✅

---

## Step 5 — Verify the Schedule

Check that EventBridge has the rule:

```bash
aws events list-rules --name-prefix morning-brief
```

You should see the rule with schedule `cron(0 11 * * ? *)` — that's **11:00 UTC = 6:00 AM Panama**.

---

## Cost Estimate

| Resource | Usage | Cost |
|---|---|---|
| Lambda invocations | 30/month | **Free** (1M free/month) |
| Lambda compute | ~60s × 30 | **Free** (400K GB-sec free) |
| EventBridge rules | 1 rule | **Free** (1M events free) |
| Anthropic API | ~30 calls/month | ~$1–2/month |

**Total AWS cost: $0.00/month** ✅

---

## Updating the Function

After any code changes:

```bash
sam build && sam deploy
```

---

## Troubleshooting

**Email not arriving?**
- Check Gmail App Password is correct (no spaces)
- Check spam/junk folder
- Look at Lambda logs: `aws logs tail /aws/lambda/ai-morning-brief --follow`

**Lambda timeout?**
- Increase timeout in `template.yaml` (currently 180s)
- Redeploy with `sam build && sam deploy`

**API errors?**
- Verify Anthropic API key is valid at https://console.anthropic.com
- Check you have credits available

---

## Managing the Schedule

```bash
# Pause the brief temporarily
aws events disable-rule --name morning-brief-daily-6am-panama

# Resume
aws events enable-rule --name morning-brief-daily-6am-panama

# Delete everything
sam delete --stack-name morning-brief
```

---

*Generated for AWS Lambda + EventBridge • Python 3.12 • Anthropic claude-sonnet-4*
