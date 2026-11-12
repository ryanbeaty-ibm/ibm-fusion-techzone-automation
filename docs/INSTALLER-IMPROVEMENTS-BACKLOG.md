# IBM Fusion Lab 01 — Installer improvement backlog (after v2.3 validation)

These items are **proposed changes for the next installer code release**, not features of the currently published v2.3 ZIP. Documentation was updated separately before modifying installer code.

## High priority — credentials fail fast

1. Prompt for `Scale GUI password (hidden)` and `Confirm Scale GUI password (hidden)`; require exact matching entries, re-prompt on mismatch, and never print/log secrets.
2. Perform an early **real** Scale REST API authentication/authorization test (e.g., `/scalemgmt/v2/info` and an endpoint suitable for remote-cluster registration). Two matching passwords alone do not establish that the password works.
3. Run the check from a network location that actually reaches the TechZone private Scale GUI. The external Ubuntu Ansible VM may be unable to reach `10.10.10.202` while OpenShift workers can.
4. Surface meaningful `401 Unauthorized` and `403 Forbidden` errors immediately. Do not wait 30 minutes for a known rejected credential.
5. Verify the account has permissions for the actual remote client registration operation, not just a read-only `/info` request.

## Recovery ergonomics

- Document and test `--update-scale-credentials --from scale-external` on an existing failed deployment.
- Consider stage-specific authorization so `--claim-disks` and `--allow-worker-reboots` are not required when the resume stage cannot touch those resources; maintain strict safety gating for every destructive action.
- Report both `Ready` and `Available` condition details during retry and after remote connection; investigate intermediate `Ready=True` with `Available=False`.
- Clearly report whether local Vault credentials and the Kubernetes GUI Secret were refreshed.

## Usability and release discipline

- Include release version, stage names, and log paths in a concise final summary.
- Re-run an entire fresh-cluster deployment after installer changes, with an intentionally bad GUI password as a negative test and a good password as a positive test.
- Keep the original v2.3 validated package and release immutable; publish changed installer code as a **new version**, with a new release asset and honest validation status.

## v2.4 candidate implementation (November 12, 2026)

- **Implemented, offline-tested:** Double hidden password confirmation and mismatch retries (maximum three); no Vault write until credentials match.
- **Implemented, offline-tested only:** Early read-only Scale `/scalemgmt/v2/info` authentication from a short-lived non-TTY OpenShift worker debug pod, with credentials streamed over stdin. Needs live TechZone validation.
- **Still pending:** Early validation of all later registration permissions, elimination of unnecessary stage-resume safety flags, improved stage-level 401/403 diagnostics, and new fresh-environment acceptance testing.
