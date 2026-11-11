# 03 — Troubleshooting and safe recovery

Use the **first failing stage**, not just the final application pod's status. This project is designed to stop when a prerequisite is missing.

| Symptom | Likely diagnosis / next step |
|---|---|
| `oc` cannot authenticate or wrong cluster | Verify the explicit kubeconfig path, `oc whoami`, API endpoint, node prefix, and nine-node inventory. |
| Fusion/ODF stage errors | Capture the first failing Ansible task and the associated operator/StorageCluster conditions. Do not delete a StorageCluster to retry. |
| Scale MCP remains Updating | MachineConfig changes may reboot selected worker nodes. Check `oc get mcp` and node readiness; Ceph infra nodes are deliberately separate. |
| Scale Operator CSV is `Succeeded`, but Deployment shows `0/0` | The Operator has been installed but controller replicas may be deliberately zero. The activation playbook changes this; confirm it reaches 1/1 before continuing. |
| Scale core pods are not Ready | Check `oc -n ibm-spectrum-scale get pods -o wide` and core-pod diagnostics before proceeding to RemoteCluster. |
| Remote server connection fails | Verify that the current TechZone reservation has the expected **pre-deployed** server, network reachability, GUI user privileges, certificate handling, and its existing filesystem `fs1`. A `401` with no authentication during connectivity probing only proves the endpoint responded. |
| PVC remains Pending, writer pod unschedulable | Investigate `oc describe pvc`, CSI provisioner logs and StorageClass parameters. The pod's `unbound immediate PersistentVolumeClaims` message is a consequence, not root cause. |
| CSI complains `filesystem fs1 in not known to primary cluster` or rejects `fs1-<id>` | Check the `volBackendFs` value. The working lab used the **local mount resource name** `<cluster>-external-scale-fs1`, not `fs1` or `fs1-<remote-cluster-id>`. |
| CLI output contains `Set-Cookie` or authorization fields | Redact before posting to issues, chat, GitHub, or attaching logs. |

## Pinpoint the failure

```bash
cd ~/fusion-lab01-installer
ls -lt work/*/logs/install-*.log | head
# Inspect the first ERROR/fatal/FAILED section before deciding on a resume stage.
```

When resuming, provide the **same cluster, kubeconfig, Scale host and Ceph disk arguments**, together with the two original authorizations. The `--from` option skips earlier stages; **it does not guarantee they are still healthy**.

Do not run the historical `reference/` playbooks directly. They were retained for traceability and may contain pinned references to prior TechZone reservations.
