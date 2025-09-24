# Security Policy

## LLM Data Handling
- Sanitization scripts (`ci/sanitizers/`) MUST run before any data is transmitted to external APIs.
- Personal information (names, emails, sensitive notes) MUST be redacted automatically; manual overrides are prohibited.
- If sanitization fails, workflows MUST stop and emit actionable errors before calling the OpenAI Responses API.

## Secrets Management
- Store `OPENAI_API_KEY`, `OPENAI_ORG`, and other credentials exclusively in GitHub repository secrets.
- Never commit secrets or raw response payloads to the repository.
- Rotate keys immediately if unauthorized access is suspected.

## Incident Response
- File a security issue within this repository if sanitization gaps or leaked sensitive data are discovered.
- Document remediation steps in `ci/compliance-checklist.md` and notify maintainers.
