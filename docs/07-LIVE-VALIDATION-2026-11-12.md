# IBM Fusion Lab 01 v2.3 — Fresh TechZone validation, November 12, 2026

**Result: PASS after corrected Scale GUI password and stage-level recovery.** This is an end-to-end **installation/persistent-storage** validation, **not** an uninterrupted one-command first-attempt success and not validation of the entire workbook.

## Tested environment

| Item | Tested value |
| --- | --- |
| Date | November 12, 2026 |
| Installer asset | `IBM-Fusion-Lab01-OneCommand-v2.3.zip` |
| Target | Fresh nine-node TechZone reservation, OCP 4.21.24 |
| Topology | 3 masters, 3 Ceph infrastructure workers, 3 Scale application workers |
| Ceph disk | Explicit disposable disk `/dev/vde` on the three infrastructure nodes |
| External Scale server | Existing TechZone VM, REST GUI at `10.10.10.202:443`, filesystem `fs1` |
| Scale StorageClass | `fusionfs1` |
| IBM Fusion Operator | `isf-operator.v2.14.1`, Succeeded; eight expected deployments Ready |
| Fusion configuration | SpectrumFusion resource present; license accepted; Global Data Platform (GDP) disabled |

The existing external IBM Storage Scale server was **not installed or rebuilt** by the automation.

## Stage results

| Stage | Status | Evidence |
| --- | --- | --- |
| `fusion-ceph` | PASS | Fusion operator and Ceph deployed |
| `ceph-io-test` | PASS | Ceph persistent storage test passed |
| `scale-nodeprep` | PASS | Scale worker preparation completed |
| `scale-operator` | PASS | Operator installed and ready |
| `scale-client` | PASS | Three Scale core pods ready |
| `scale-external` | PASS **on recovery** | RemoteCluster `Ready=True`; external `fs1` mounted; StorageClass verified; Scale CSI persistence test passed |
| `final-verification` | PASS | Read-only checks of Fusion and Ceph health |

## Failure encountered and recovery

The original deployment completed the first five stages but `scale-external` waited 30 minutes and failed to reach RemoteCluster `Ready=True`. The RemoteCluster showed `401 Unauthorized` and `403 Forbidden` responses from external Scale REST endpoints. A test from the separate Ubuntu automation VM timed out because that VM did not have direct network access to the private Scale address; a test from within the TechZone network confirmed reachability.

The `csi-storage-gui-user` account on the existing Scale VM was active with the expected GUI groups and **zero failed login attempts**. Re-entering the guide-provided password carefully produced `HTTP 200`, confirming a working REST login. The exact mistype from the original attempt is not recoverable, but a stored credential mismatch is the leading explanation for the original failure.

After running `deploy --update-scale-credentials --from scale-external` **with the two v2.3 mandatory authorization flags**, the installer reused its pinned workspace and resumed at the failed stage. This recovery took **3m 03s excluding preflight and credential entry**, with all recovered-stage tasks succeeding.

## Persistent storage verification

- Remote Scale cluster registered and reported `Ready=True`.
- Existing external `fs1` filesystem mounted into the OpenShift Scale client.
- `fusionfs1` StorageClass configured with the verified **local mounted Filesystem custom-resource name** and a **live-discovered** remote cluster ID.
- Container Storage Interface (CSI) provisioned a test persistent volume claim.
- Writer pod wrote **16 MiB** and recorded a checksum.
- Writer pod was deleted; reader pod remounted the volume.
- SHA-256 checksum verified persisted data (`READ_OK`).
- Temporary test namespace, pods and claim were cleaned up.
- Final verification confirmed **Fusion Operator Succeeded**, **eight Fusion deployments ready**, **Ceph StorageCluster Ready**, **three OSD pods**, and **Ceph RBD StorageClass**.

Installer final line:

```text
PASS: ALL LAB 01 INSTALLATION AND STORAGE TEST STAGES.
```

**Caveat for follow-up:** An intermediate RemoteCluster display had `Ready=True`, `Available=False`, even though the filesystem mount and actual data I/O subsequently succeeded. An additional post-run `Available` condition check may be useful to distinguish transient reconciliation from an ongoing warning.

## Lessons for documentation and upcoming installer changes

The GitHub Quick Start needs direct instructions for downloading/transferring the packaged installer and kubeconfig; finding TechZone Environment ID, Scale VM IP and GUI credentials; distinguishing `plan` from `deploy`; entering the single hidden password prompt; expected installation duration; and resuming a failed stage. The **next installer code release** should add password confirmation and early real API authentication from a reachable network location. Neither change is present in the validated v2.3 package.
