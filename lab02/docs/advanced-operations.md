# Advanced Ansible stage operations (troubleshooting only)

If this is your first run, follow the [numbered Lab 02 guide](LAB02-BACKUP-AND-RESTORE.md) instead of executing individual playbooks.

The normal run is a **single command** from `lab02/`: `bash scripts/run-lab02.sh`. This page is for isolating a failing step, preserving evidence, or rerunning verification. **Don't execute every block below during a normal lab.**

### Advanced: manually run just one Ansible stage (troubleshooting only)

For debugging, the stage runner also supports individual playbooks:

```bash
./scripts/run-stage.sh 01 syntax
./scripts/run-stage.sh 01 check
./scripts/run-stage.sh 01 run

./scripts/run-stage.sh 02 check
./scripts/run-stage.sh 02 run
./scripts/run-stage.sh 03 run
./scripts/run-stage.sh 04 run
```

Wait for each stage to complete and inspect its results before starting the next. `--check` runs preflight on the application playbooks and **intentionally skips backup/restore and hash proof**. Execute normally to prove data integrity. Most polling intervals are 15 seconds; 30-minute waits are upper bounds, not delays.

### Service Protection manual interlude (05)

Normally the single runner handles 05a preparation and 05c preflight automatically; you only configure the storage and schedule in Fusion GUI (05b).

Follow [docs/manual-checkpoints.md](manual-checkpoints.md) for a dedicated OBC on the second cluster, TLS certificate handling, exact Fusion UI fields and schedule. Then run this *read-only* prerequisite verifier:

```bash
ansible-playbook -i localhost, -c local installer/05-service-protection-preflight.yml \
  -e @config/environment.yml
```

This confirms storage inputs, **not** that IBM Fusion created a successful service backup. Verify status and available backup count in the Fusion UI; do not claim end-to-end automation of this UI-only feature.

### Spoke bootstrap manual interlude (06)

Normally the single runner handles 06b installation automatically; you only generate/download the connection manifest in Fusion GUI (06a).

From the **hub UI**, download the IBM-generated `BackupAndRestoreAgentDeployment.yaml`, copy it onto Ubuntu, and set `chmod 600`. Deploy only to the spoke. We originally validated the explicit `oc --kubeconfig="$HOME/.kube/lab01.conf" apply -f ...` command. An optional Ansible wrapper for future runs:

```bash
ansible-playbook -i localhost, -c local installer/06-spoke-agent-bootstrap.yml \
  -e @config/environment.yml \
  -e "generated_spoke_manifest=$HOME/BackupAndRestoreAgentDeployment.yaml"
```

**Do not use the generated YAML after its token expires (~1 hour).** Never commit or paste the generated file. Confirm the **hub UI Topology** displays the second cluster `Connected / Healthy`.

### Cross-cluster application restore (07)

After the hub has a successful FileBrowser S3 backup, the spoke agent is connected, the spoke can reach the hub S3 route, and its destination `filebrowser` namespace is free (or owned by the matching restore):

```bash
./scripts/run-stage.sh 07 syntax
./scripts/run-stage.sh 07 check
./scripts/run-stage.sh 07 run
# Repeat the exact same command to confirm idempotency.
./scripts/run-stage.sh 07 run
```

The Restore custom resource is created **on the hub** using the registered spoke's `targetCluster`. The playbook refuses to overwrite a namespace on the spoke if the matching managed restore is absent, and refuses conflicting Restore objects. It then verifies the source and recovered SHA-256 hashes. See [validation evidence](../evidence/validated-runs.md).


## Resume whole workflow after a failure

```bash
bash scripts/run-lab02.sh --from 05a
bash scripts/run-lab02.sh --from 05c
bash scripts/run-lab02.sh --from 06b
bash scripts/run-lab02.sh --from 07
```

Choose **one** appropriate resume stage, not all commands.
