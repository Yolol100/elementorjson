# Security policy

This repository is a public, disposable Elementor QA harness. It is not a production WordPress plugin distribution and must never contain customer-confidential material or credentials.

## Repository rules

- Never commit Elementor Pro license keys, Composer auth files, private package URLs, WordPress credentials, tokens, personal data, client-confidential Elementor JSON, private screenshots or unsanitized target inventories.
- Keep GitHub Actions permissions read-only except for an explicitly temporary maintenance workflow that is removed before merge.
- Pin third-party/GitHub Actions by full commit SHA and keep `package-lock.json` committed.
- Use `npm ci` in CI and fail on high/critical npm audit findings.
- Pro CI requires both the `ELEMENTOR_PRO_LICENSE_KEY` secret and an explicit `ELEMENTOR_PRO_VERSION` repository variable.
- Production/staging mutations are out of scope for this repository.

## Recommended GitHub repository settings

Repository administrators should enable branch protection/rulesets for `main`, require both QA jobs before merge, block force pushes/deletions, enable Dependabot alerts/security updates, secret scanning/push protection where available, and code scanning where appropriate. These account-level settings are verified separately from repository source.

## Reporting

Do not open a public issue containing a credential or confidential customer artifact. Revoke/rotate any exposed credential first and use a private channel available to the repository owner.
