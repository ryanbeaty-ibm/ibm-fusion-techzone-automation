# Evidence from live TechZone validation — November 12–13, 2026

The values below are **observed lab results**, not claimed automatic tests of this consolidated distribution. Some consolidated source files have been changed to support portable cluster identity configuration; their original successful executions predate this packaging.

| Stage | Observed validation | Notes |
|---|---|---|
| 01 hub install | `FusionServiceInstance` Completed; 22 hub deployments available | Original v0.1 task execution |
| 02 S3 setup | `hubspoke-bucket` Connected; `daily-snapshot` and `weekly-backup` policies | Original v0.2 `ok=31 changed=5 failed=0`; `oc apply` may still report changes on rerun |
| 03 FileBrowser | Backup Completed, 8,454,144 bytes; alternate restore Completed; SHA-256 matched | Corrected v0.3 rerun: `ok=34 changed=0 failed=0` |
| 04 MongoDB | `fsyncLock`, volume snapshot/backup, `fsyncUnlock`, S3 restore, UID repair, SHA-256 passed | v0.4.4 fresh run: `ok=71 changed=11 failed=0`; rerun: `ok=52 changed=0 failed=0` |
| 05 Service Protection | Dedicated OBC on second cluster Bound; hub S3 location Connected; first service backup Completed | UI configuration; daily 12–4 AM America/Los_Angeles, 30-day retention. Full control-plane recovery **not** tested |
| 06 Spoke | Generated YAML applied with explicit spoke kubeconfig; agent service instance Completed; 8/8 deployments available | Hub Topology: spoke Connected / Healthy |
| 07 Cross-cluster FileBrowser | Hub Restore `filebrowser-lab02-v07-restore` Completed, spoke `filebrowser` running, both PVCs bound, data checksum identical | Initial restore created with `oc`; Ansible v0.7 read-only adoption/verification `ok=21 changed=0 failed=0` |

## FileBrowser proof

Source hub namespace: `filebrowser` on `itz-t63twk`; recovered spoke namespace: `filebrowser` on `itz-2xvmb0`. Filename `/files/lab02-proof-v03.bin`, 8 MiB.

SHA-256 on **both** clusters:

```text
caf85e4ede776f0a8ab82bae96ae0ec126f8ce8f3fb8ff6c0dcc8c585a2d608b
```

## Deliberately unresolved / nonvalidated claims

- Stage 05 new preflight and stage 06 new Ansible bootstrap helper are statically validated but have **not been executed on the live environment**; the corresponding manual/`oc` steps were validated.
- The consolidated reparameterized stage 01–04 scripts have not been rerun as a complete fresh multi-stage installation after packaging.
- Stage 07's *fresh* Restore CR creation path was not exercised from Ansible; a matching Restore was created via `oc` and then adopted and verified by Ansible.
- No destructive full restore of the Backup & Restore Service Protection control plane was performed.
- A single test payload checksum proves data integrity for that payload, not general workload/application consistency under every condition.


## Consolidated guided runner (added Nov 13, 2026)

The single-command `scripts/run-lab02.sh` and new stage 05a Service Protection preparation playbook were created after the live v0.7 test. They passed static validation and are **not yet full-run live validated**. The underlying stages 01–04 were previously live tested individually, the Service Protection UI flow and OBC/certificate operations were done manually, and v0.7 existing-restore adoption was live tested with `changed=0 failed=0`. Do not conflate those results with a fresh run of the wrapper.
