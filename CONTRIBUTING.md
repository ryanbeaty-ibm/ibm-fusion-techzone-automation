# Contributing

This is a lab automation project, not an official IBM-supported product. Keep changes scoped to disposable TechZone environments and preserve fail-closed safety checks.

1. Open an issue describing the target template, OpenShift/Fusion version, and desired change **without** secrets or raw logs.
2. For a code change, add or update an offline test under `tests/` and run the validation commands in the README/CI workflow.
3. Document whether a change was verified offline or in a **fresh** cluster. Do not claim live validation based solely on unit tests or an earlier release.
4. Preserve the `plan` read-only property and require deliberate disk/reboot authorization. Never turn a safety failure into a silent skip.
5. Keep user-specific state, manifests generated under `work/`, kubeconfigs, password files and debug logs outside Git.

Do not directly run archived `reference/` playbooks against a new cluster. The installer compiles a cluster-pinned workspace first.
