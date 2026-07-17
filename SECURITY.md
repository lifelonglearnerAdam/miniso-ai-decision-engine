# Security Policy

## Supported scope

This repository is a competition prototype and reference implementation. It is
not approved for processing production consumer data, confidential product
plans, personal information, supplier contracts, or credentials.

## Reporting a vulnerability

Please open a private GitHub security advisory for this repository. Do not put
secrets, personal information, exploit payloads, or unreleased business data in
a public issue.

## Production hardening requirements

Before any enterprise pilot, the owner must complete threat modelling, data
classification, least-privilege service identities, secret management,
dependency and container scanning, immutable audit logging, model/input/output
monitoring, prompt-injection testing, human approval gates, rollback drills and
legal review for privacy, copyright and IP licensing.

The design guidance in [docs/07_安全治理与生产化.md](docs/07_安全治理与生产化.md)
is a starting control set, not a compliance certification.
