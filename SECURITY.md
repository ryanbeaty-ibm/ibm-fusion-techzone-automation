# Security and intended use

This project can change host configuration, **consume selected disks**, create storage resources and **reboot worker nodes**. Use it **only** in a disposable, correctly identified IBM TechZone lab.

## Guardrails and limitations

- The launcher requires an explicitly named kubeconfig, expected API hostname, `system:admin` identity and nine expected Ready nodes.
- `plan` reads cluster state and creates local files; `deploy` requires `--claim-disks` and `--allow-worker-reboots`.
- The deployment playbooks inspect the selected Ceph disks before claiming them. **The operator must still confirm that these are disposable devices.**
- Credentials are entered interactively and saved as encrypted Ansible Vault values **outside** the Git repository, with a separate local unlock key. Anyone with access to both files can decrypt the credentials.
- The generated `work/` folder may contain operational diagnostics, inventory, URLs, and logs. It is Git-ignored, not automatically safe to publish.
- Never upload kubeconfig contents, passwords, Vault unlock keys, credentials, session cookies, HTTP authorization headers, or unsanitized support bundles.

## Before a public repository release

Review **the entire Git history**, not just the latest working tree; inspect historical `reference/` source for reservation-specific names and for any third-party material that cannot be redistributed. `.gitignore` cannot remove previously committed secrets. Choose an appropriate license for the original automation and verify IBM ownership/branding boundaries before opening the repository publicly.

For potentially sensitive reports, use a private channel to the maintainer rather than public GitHub issues. Do not paste raw deployment logs into issues.
