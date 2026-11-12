# Changelog

## v2.4.0 — Password confirmation + early Scale API preflight (November 12, 2026; pre-release)

- Prompt for the Scale GUI password **twice**, with hidden input; retry mismatches up to three times and fail before saving.
- Authenticate new or explicitly updated credentials **early from an OpenShift worker** using a temporary `oc debug -T` pod and a read-only `/scalemgmt/v2/info` request. This is needed because the external Ubuntu VM cannot reach the private Scale GUI address directly.
- Stream credentials into curl over non-TTY stdin, not command-line arguments, environment variables, or project files. Fail fast on HTTP 401/403; do not overwrite a working Vault file after unsuccessful validation.
- Standardize new release extraction directory as `$HOME/fusion-lab01-v2.4`, without nested `lab01/` directories.
- Update Lab 1 instructions and retain prior v2.3 validation records.

**Validation:** Offline Python, YAML and shell checks passed. The new worker-side live credential preflight and full v2.4 deployment **have not yet been validated in TechZone**. Do not describe v2.4 as fresh-lab validated. The previous v2.3 succeeded on November 12 after a corrected GUI password and recovery from `scale-external`.


<!-- BEGIN DOCS V3.3 LAYOUT -->
## 2026-11-12 - Repository navigation cleanup (documentation only)

- Moved Lab 1 Quick Start instructions from the project home page to `docs/LAB01-INSTALLATION-AND-CONFIGURATION.md`.
- Linked the Lab 1 roadmap entry to that dedicated guide and retained the old Start Here URL as a pointer.
- Updated introductory prerequisite links. No changes to the v2.3 installer or release ZIP.
<!-- END DOCS V3.3 LAYOUT -->


<!-- BEGIN DOCS V3.2 CHANGELOG -->
## 2026-11-12 â€” Documentation and v2.3 validation (no installer code change)

- Documented a successful fresh OCP 4.21.24 Lab 1 end-to-end storage validation after recovering from incorrect external Scale GUI credentials.
- Improved README Quick Start: packaged ZIP transfer, kubeconfig transfer, discovery of TechZone Environment ID and Scale address, read-only plan vs deployment, interactive credentials, timing and success criteria.
- Added external Scale API troubleshooting, correct `itzuser`/Bastion Password VM login, safe `--update-scale-credentials --from scale-external` resume, and a future installer-improvements backlog.
- Linked the Lab 1 roadmap entry to installer instructions. Preserved previous v2.2 validation history.
<!-- END DOCS V3.2 CHANGELOG -->


## v2.3.0 — Cleanup candidate (November 11, 2026)

- Wait for the IBM Storage Scale operator's ready replica instead of immediately asserting a transient `readyReplicas=0` condition after rollout.
- Iterate over Kubernetes node **names**, not full node objects, in the Scale pool exclusion assertion. Prevents enormous Ansible `item` output while keeping the protection.
- Print and log per-stage deployment durations and total installer time (excluding preflight and credential entry).
- Fix malformed `.gitignore` Vault patterns and add regression checks for ignored sensitive artifacts.
- Refresh documentation, field-test evidence, and GitHub project layout; add local continuous-integration checks.

**Testing:** Python/shell/YAML/static/offline source checks only; needs a new clean-room deployment for v2.3 live acceptance.

## v2.2.0 — Fresh-cluster validated (November 11, 2026)

- Automatic read-only OpenShift health gate in `plan` and `deploy`.
- Successful single-command installation on a new TechZone OCP 4.21.24 reservation.
- All seven stages passed; Ceph and Scale 16 MiB persistent-storage tests passed.
- Operator activation initially saw a transient not-ready status; the existing wrapper retry succeeded.
- Observed total approximately 40 minutes.

## v2.1.0

- Pinned workspace, exact API/cluster identity checks, per-cluster encrypted Ansible Vault credentials, and stage-specific resume.
- Included the previously tested component scripts and corrected remote Scale StorageClass backend logic.
