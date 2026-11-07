# Security Policy

## Supported scope

Security reports are welcome for the current public default branch.

## Reporting a vulnerability

Please do not publish credentials, exploit details or private user data in a public issue. Use GitHub's private vulnerability reporting feature for this repository when available. If private reporting is unavailable, contact the repository owner through the email listed on the GitHub profile and share only the minimum information needed to establish contact.

## Sensitive data

Never commit:

- API keys, passwords, JWT signing keys or bearer tokens
- `.env` files or machine-specific configuration
- Personal memory, conversation history, audio recordings or local database contents
- Model weights, private logs or backups

If a secret is committed, deleting it from the latest revision is not enough. Revoke or rotate it first, then coordinate history cleanup and review all branches, tags, forks and deployment copies.

## Desktop agent

The desktop agent can trigger local actions. Keep it bound to localhost unless remote access is deliberately secured, use a unique token, and restrict the application allowlist to the minimum required set.
