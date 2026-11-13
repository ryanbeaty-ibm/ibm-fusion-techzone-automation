# Troubleshooting verified during this lab

| Symptom | Cause or investigation | Safe response |
|---|---|---|
| S3 `403` from `curl` | Unauthenticated request reached an S3 service | Connectivity passes; verify credentials separately in Fusion |
| S3 location fails with `Invalid PEM format No EOL char found in footer` | Certificate Secret missing real trailing newline or contains literal `\n` | Validate certificate PEM and correct its formatting; avoid exposing credentials |
| `fbackup` phase `RecipeFailed` and shell `Syntax error: then unexpected` / `Syntax error: ( unexpected` | MongoDB recipe hook command was parsed as shell text incorrectly | Use the bundled, validated `mongodb-recipe-v0.4.yaml` with the proper quoted command syntax |
| MongoDB restored pod `CrashLoopBackOff`, WiredTigerHS.wt `Operation not permitted` | Source and target namespaces assigned different UID ranges | v0.4.4 recovers by repairing ownership on **restored PVC only** with temporary, scoped SCC access |
| Recovery Job has condition `SuccessCriteriaMet` | Kubernetes can report this before a condition named `Complete` | The validated poller checks `status.succeeded >= 1` rather than first conditions array element |
| FileBrowser `oc apply` reports Deployment `configured` but `oc diff` is empty | Manifest reconciliation can report changes on repeated apply | v0.3 playbook detects drift first; validated repeat `changed=0` |
| `oc get cluster` returns none | Query searched wrong namespace | Use `oc --kubeconfig=<hub> get cluster -A`, then verify exact spoke registration in hub Topology |
| Spoke deployment fails to connect | Bootstrap token expiry or hub Kafka reachability | Generate a **new** one-hour token from Hub Topology, verify kubeconfig points to spoke, review routes |
| Restore completed but app unavailable | Kubernetes volume permissions, readiness or container initialization | Inspect pod `--previous` logs, PVC and events; avoid deleting database files or blindly restarting storage |

## Read-only status commands

```bash
HUB="$HOME/.kube/lab02.conf"; SPOKE="$HOME/.kube/lab01.conf"
oc --kubeconfig="$HUB" -n ibm-spectrum-fusion-ns get fbackup,frestore
oc --kubeconfig="$HUB" get cluster -A
oc --kubeconfig="$SPOKE" -n ibm-spectrum-fusion-ns get fusionserviceinstance
oc --kubeconfig="$SPOKE" -n ibm-backup-restore get deployments
oc --kubeconfig="$SPOKE" -n filebrowser get pods,pvc
```

Use `watch -n 15 -d '...'` for auto-refresh. `FAILED - RETRYING` during Ansible polling means a task has not met its success condition *yet*; inspect the Fusion resource phase before assuming a real failure.
