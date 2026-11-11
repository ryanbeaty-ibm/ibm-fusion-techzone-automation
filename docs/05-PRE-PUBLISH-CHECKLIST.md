# 05 — Before publishing to GitHub

**v2.1 candidate:** The installer now prompts for the Scale GUI username and hidden password and encrypts them with Ansible Vault outside the project. There is no hardcoded Scale GUI password in the shipped playbook. Before publishing, audit your entire Git working tree and history for secrets and verify the Vault flow on a new lab.

## Release checklist

- [ ] Externalize all hardcoded GUI passwords, API tokens and private key material. Avoid echoing them or putting them in command-line process arguments.
- [ ] Review entire tracked tree, history, and generated artifacts for credentials. `.gitignore` does not protect credentials already checked in.
- [ ] Exclude `work/`, logs, captured HTTP responses, `.kube/`, kubeconfig files, private keys, secrets and environment files.
- [ ] Verify the public source doesn't embed any active access URL that itself grants access.
- [ ] Do not publish IBM course PDFs, proprietary templates, or other third-party copyrighted materials unless you have redistribution rights.
- [ ] Add an explicit license for **your original automation** only after choosing the appropriate terms; do not claim ownership of IBM intellectual property.
- [ ] Explain that the scripts are intended for disposable TechZone labs, not production.
- [ ] Do not claim the v2.1 single-command installer is validated until the fresh-lab test passes; record the new cluster and outcome in a sanitized release note.
- [ ] Review the `reference/` archive: historical scripts may contain stale cluster names and should not be executed directly.
- [ ] Validate the README commands from a clean checkout.

## Local secret management plan (to implement before publication)

For disposable private lab use, credentials can remain in a local ignored variables file, e.g. `config/local/scale-secrets.yml`, supplied to the remote-connection playbook without being committed. Prefer Ansible Vault or an environment-backed secret for broader sharing. The v2.1 installer supports a per-cluster encrypted Ansible Vault variables file; its randomly generated unlock key is stored separately outside the repository. Both stay private. Verify the GitHub tree and history contain neither file.

## Suggested GitHub repository description

> Automated IBM Fusion, Ceph, and external IBM Storage Scale client deployment for disposable IBM TechZone OpenShift labs. Includes guarded provisioning, stage-based recovery and end-to-end persistent-storage tests. Independent community project; not an official IBM installer.
