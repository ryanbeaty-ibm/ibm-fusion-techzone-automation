# IBM Fusion — Lab 01: Single-command TechZone installer (v2.1)

## Result from the completed lab

The *installation/storage-validation portion* of IBM's **Installation and Configuration** lab passed on `itz-s6fyum` (OpenShift 4.21.24) on 11 November 2026:

- IBM Storage Fusion 2.14.1 and IBM Fusion Data Foundation/Ceph installed.
- Three Ceph Object Storage Daemons (OSDs) Ready; 16 MiB Ceph block volume persisted across pod deletion and remount with matching SHA-256.
- IBM Storage Scale Operator 60.1.0 activated, three prepared Scale workers and three Ready Scale core pods.
- Pre-deployed external IBM Storage Scale server connected; remote `fs1` mounted as **`lab01-external-scale-fs1`**.
- `fusionfs1` StorageClass corrected to **`volBackendFs: lab01-external-scale-fs1`**, the **local mounted filesystem name**, while `clusterId` is discovered live. Scale CSI PVC bound; 16 MiB written, remounted into a new pod, and checksum verified; test namespace cleaned up.

The final successful run was `bash scripts/lab01-scale-finish.sh finish` from v1.4.2. **That proves the current lab worked, not that this newly consolidated v2.1 entry point has been field-tested on a fresh cluster.** It needs a clean-room test on a future TechZone reservation.

## What you received

- `install-lab01.sh`: single command entry point, with `plan` and `deploy` actions.
- `installer/techzone_lab01.py`: discovers and validates the **new** cluster's API, version, administrator, and EXACT node names; builds a separate pin-checked workspace; invokes the original successful stages in order and logs output.
- `reference/`: read-only source copy of the uploaded working playbooks, scripts and templates, with the v1.4.2 StorageClass correction. The installer does not execute historical old-lab playbooks directly.
- `docs/` and `.gitignore`: GitHub documentation and rules protecting runtime files from commits.
- `work/<cluster-prefix>/`: generated automatically when running the command. The generated workspace is pinned to the actual kubeconfig/API and checked cluster. It is intentionally never overwritten if its settings change; this prevents accidental cross-cluster re-use.

## Keep it in Dropbox, deploy from Ubuntu

Copy the ZIP into `D:\Dropbox\Fusion` for backup, then use **SecureCRT SFTP**:

```text
lcd D:\Dropbox\Fusion
cd /home/automation
put IBM-Fusion-Lab01-OneCommand-v2.1.zip
```

On your existing Ubuntu automation server:

```bash
mkdir -p ~/fusion-lab01-installer
cd ~/fusion-lab01-installer
unzip -o ~/IBM-Fusion-Lab01-OneCommand-v2.1.zip -d .
```

### One deployment command for the NEXT clean TechZone lab

**Replace the values** with the new reservation's cluster prefix, kubeconfig and Scale management IP. **Check that `/dev/vde` is the three disposable blank infrastructure disks on that reservation.**

```bash
cd ~/fusion-lab01-installer
bash install-lab01.sh deploy \
  --cluster itz-NEWCLUSTER \
  --kubeconfig /home/automation/.kube/newlab.conf \
  --scale-host 10.10.10.202 \
  --ceph-disk /dev/vde \
  --claim-disks \
  --allow-worker-reboots
```

The explicit flags `--claim-disks` and `--allow-worker-reboots` authorize potentially destructive disk provisioning and rolling Scale worker reboots, respectively. **Do not run this installer against a production or data-bearing system.** This release refuses non-TechZone API hostnames or mismatched node identities and requires OCP 4.21.x and `system:admin`.

### Optional preview, no cluster changes

```bash
bash install-lab01.sh plan \
  --cluster itz-NEWCLUSTER \
  --kubeconfig /home/automation/.kube/newlab.conf \
  --scale-host 10.10.10.202 \
  --ceph-disk /dev/vde
```

`plan` reads the cluster and generates local files only. It does not test disk blankness or connect to the Scale management server. Those are checked at the appropriate live deployment stages.

### First-run Scale GUI credential prompt (v2.1)

Before making cluster changes, the first `deploy` for a given cluster shows:

```text
=== IBM Storage Scale GUI credentials (stored using Ansible Vault) ===
Scale GUI username [csi-storage-gui-user]: 
Scale GUI password (hidden):
```

Press **Enter** for the documented username. Type the password normally; it will not appear on screen. On later deploy/resume runs for the same cluster, the installer reuses the encrypted Vault values without asking again. `plan` never asks for credentials. Use `--update-scale-credentials` to replace stored credentials when your lab reservation changes.

The random Vault key and the encrypted credentials are both saved with user-only permissions in separate directories under `~/.config/fusion-lab01/`, **not** in the installer or `work/` folder. Do not commit or share either. Keeping the key on the same host favors no-repeat prompts over defense against a compromised Ubuntu account.

### Resume after a failure

The single command is staged, and it prints the last failing stage and location of its log. After fixing the cause, rerun with the exact same options plus `--from STAGE`, where stage is one of:

`fusion-ceph`, `ceph-io-test`, `scale-nodeprep`, `scale-operator`, `scale-client`, `scale-external`, or `final-verification`.

For example, `--from scale-operator` resumes at operator activation, instead of reinstalling Ceph or relabeling workers. Only skip stages when you have verified that they completed successfully; the resume flag **does not assert previous-stage health**.

## What the command actually does

1. Pins the live TechZone API, user, OpenShift version and **exactly nine nodes** with 3 masters, 3 Ceph infrastructure workers and 3 application/Scale workers.
2. Runs the original Fusion + Data Foundation/Ceph installation, auditing **exactly the selected `/dev/vde` on the three infra nodes** before any new disk claim.
3. Tests Ceph CSI block-volume persistence by writing 16 MiB, remounting into a new pod, and comparing SHA-256 hashes.
4. Creates the isolated Scale MachineConfigPool (MCP), applies the `kernel-devel` extension (selected workers may reboot), and activates the already-installed Scale Operator. Its activation stage retries a transient readiness failure.
5. Deploys the three-node local, data-access Scale client on application workers only.
6. Connects to the **pre-deployed external Scale server** (no new server installation), mounts existing `fs1`, and **discovers** its remote cluster ID via `mmremotecluster show all`.
7. Creates `fusionfs1` with `clusterId` from live discovery and `volBackendFs` equal to the **local mounted filesystem resource** (`<generated-scale-name>-fs1`, NOT `fs1` or `fs1-<cluster-id>`).
8. Tests dynamic Scale PVC provisioning and a 16 MiB write/remount/SHA-256 checksum, cleans up its own temporary namespace, and runs final Fusion/Ceph readiness verification.

All stages are existing successful v1.2–v1.4.2 Ansible workflows **with target-specific assertions compiled for the new lab**. The Cluster and GUI secrets are not shared with an existing production installation. All changes occur against the explicit kubeconfig, not the ambient default context.

## Important boundaries

- The pre-deployed external Scale server must already exist, remain accessible from the cluster, and expose `fs1`. `--scale-host` supplies its management IP/hostname; **do not assume `10.10.10.202` is correct for every reservation**.
- At the beginning of the **first deploy per cluster**, the installer prompts for Scale GUI username (Enter accepts `csi-storage-gui-user`) and a hidden password. Both are encrypted as Ansible Vault scalar variables outside the project at `~/.config/fusion-lab01/credentials/<cluster>.vault.yml`. A separate random, 0600 Vault key is stored under `~/.config/fusion-lab01/vault-keys/<cluster>.key`, also **outside the repository**. Subsequent runs reuse them without prompting. To change them, add `--update-scale-credentials` to a `deploy` or resume command. This convenience mode protects against accidental GitHub commits and casual disclosure; a user who can read both local files can decrypt the credentials. For stronger security, use an external secret manager or keep the Vault unlock key offline.
- The backend `volBackendFs` issue is corrected in the source and preserved in generated workspaces. **Do not substitute the remote filesystem's plain name or append the remote cluster ID to it**.
- Do not copy reference playbooks straight to a new cluster and run them: some contain historically pinned TechZone names. The `install-lab01.sh` entry point generates and checks their new target identities first.
- CLI tools required on Ubuntu: `oc`, `ansible-playbook`, `ansible-vault`, `python3` with PyYAML, `jq`, `bash`, and the standard Linux tools the validated scripts invoke. Downloading the ZIP does not install tools.
- This installer covers the **Fusion, Ceph, and external Scale installation/storage validation** portion of Lab 01. It does not automatically complete any other learning exercises, quizzes, or product service workflows in the official course.
- Lab source contains no hardcoded Scale GUI password. Ansible Vault credentials and the local unlock key live in the operator's home directory outside the repository, and both must be excluded from any backup shared publicly. Lab source and generated workspaces can include operational details. Keep the Dropbox shared-folder permissions appropriate and do not publish raw logs containing HTTP headers or cookies.

## Validation performed for v2.1

Offline checks on the actual uploaded source: Python compilation, shell syntax, YAML parsing, and mock kubeconfig/`oc` discovery against a synthetic `itz-new987` nine-node cluster. The resulting compiled client and Scale manifests were inspected; the `fusionfs1` backend was verified as `<scale-name>-fs1` and the `clusterId` remained a runtime discovery variable.

**Still outstanding:** one brand-new-cluster run of the *consolidated v2.1 command*. The success of v1.4.2 on `itz-s6fyum` does not by itself establish that every automated stage will work identically in another reservation.
