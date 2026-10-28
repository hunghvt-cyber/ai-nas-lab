# Gemini API wrapper smoke check — 2026-10-28

Reusable tool note only; no application or Notes task details are included.

## Runtime evidence

- Host: NAS Debian 12 aarch64.
- Existing wrapper: `/home/admin/bin/gemini-task`.
- SHA-256 on host: `29481dc45c6461b5f993a29f7caba32871cd826c6885abcf99a4928652c8ec00`,
  matching the saved `src/gemini-task` source.
- Existing key store path and alias inventory were not read. File metadata showed
  the key store at mode `0600`; no credential value was displayed or changed.
- A real, minimal `generateContent` call through the wrapper using
  `gemini-3.5-flash-lite` and one explicitly selected alias returned the exact
  expected short response. This confirms the wrapper/API path works at that
  moment; it does not validate any unselected aliases or future quota.
- The CLI/OAuth `UNSUPPORTED_CLIENT` issue did not affect this direct API
  wrapper. No CLI retry, OAuth flow, key rotation, or credential change was
  performed.

## Reusable invocation practice

- For an availability ping, send a tiny harmless prompt through the existing
  wrapper and require an exact short response. A `--version`, TLS check, or
  models-list response alone does not prove `generateContent` works.
- Pin one approved alias with `--key keyN` when the task is only a smoke test;
  the wrapper then cannot fail over to another key. The current wrapper's
  transient 503 retries are bounded and stay on that same key.
- Keep the prompt free of private task data. Never inspect or print the key
  store. Do not rotate keys to bypass quota or a provider error.
- The wrapper's `status` command can create/update state and lock files, so
  treat it as stateful even though it does not call the API.
- Record model, route, explicit-key behavior and actual short response
  separately from CLI/OAuth status. Do not generalize one successful key/model
  test to other aliases.
