# Start here — IBM Fusion Lab 01 installer

This walkthrough is intended for an engineer who already has a working **Ubuntu Ansible control node** and wants to run the packaged IBM Fusion Lab 1 installer exactly as documented. If you **do not** have an Ansible server yet, first follow [Getting Started from Zero](docs/GETTING-STARTED-FROM-ZERO.md) and the [Hyper-V + Ubuntu prerequisite guide](docs/HYPERV-UBUNTU-PREREQUISITES.md).

> **Disposable lab only.** Deployment claims and erases selected Ceph disks and can reboot OpenShift worker nodes. Never use this workflow against a production cluster.

## 1 — Download the installer ZIP and transfer it to Ubuntu

1. Open the repository's [Releases page](https://github.com/ryanbeaty-ibm/ibm-fusion-techzone-automation/releases) and select **IBM Fusion Lab 1 — Ansible Installer v2.3**.
2. Under **Assets**, download `IBM-Fusion-Lab01-OneCommand-v2.3.zip`. Do **not** use GitHub's automatically generated **Source code (zip)**.
3. Save it to the Windows PC's `C:\Users\YOUR_USERNAME\Downloads` folder.
4. In SecureCRT **Secure File Transfer Protocol (SFTP)**, transfer the file to Ubuntu:

   ```text
   lcd C:\Users\YOUR_USERNAME\Downloads
   cd /home/automation
   put IBM-Fusion-Lab01-OneCommand-v2.3.zip
   ```

5. In the Ubuntu **SSH** terminal, extract and confirm the installation script:

   ```bash
   mkdir -p "$HOME/fusion-lab-v2.3"
   unzip -o "$HOME/IBM-Fusion-Lab01-OneCommand-v2.3.zip" -d "$HOME/fusion-lab-v2.3"
   cd "$HOME/fusion-lab-v2.3"
   ls -l install-lab01.sh
   ```

The paths `/home/automation` and `$HOME` assume the documented Ubuntu username `automation`. Adapt the remote path if you use a different Linux account. Use a new versioned directory rather than overwriting an older validated installation.

## 2 — Download the kubeconfig from TechZone and upload it

1. Open the **TechZone reservation** that you intend to use for Lab 1.
2. Under **Download kubeconfig**, click **Download**.
3. Save the file locally as a recognizable filename, for example **`lab01.conf`**, in `C:\Users\YOUR_USERNAME\Downloads` (outside the GitHub repository).
4. In **Ubuntu SSH**, create and protect the directory **before** uploading:

   ```bash
   mkdir -p "$HOME/.kube" && chmod 700 "$HOME/.kube"
   ```

5. In **SecureCRT SFTP**, enter:

   ```text
   lcd C:\Users\YOUR_USERNAME\Downloads
   cd /home/automation/.kube
   put lab01.conf
   ```

6. Back in **Ubuntu SSH**, test cluster connectivity:

   ```bash
   chmod 600 "$HOME/.kube/lab01.conf"
   oc --kubeconfig="$HOME/.kube/lab01.conf" whoami --show-server
   oc --kubeconfig="$HOME/.kube/lab01.conf" get nodes
   ```

You should see the API URL and nodes for your **current** reservation. Use the filename you chose throughout the rest of the guide.

## 3 — Obtain the lab information for the commands

1. Open **TechZone reservation → Outputs** and record the **Environment ID** (for example `itz-REPLACE_ME`). This is the `--cluster` value.
2. Click **VM Remote Console** and locate the existing `xxx-scale-2` (sometimes shown as `xxx-scale-02`) VM. Copy the **IP Address** (commonly `10.10.10.202` in the guide). This is `--scale-host`.
3. Open the IBM Fusion Installation and Configuration lab guide. Labeled **page 30** has the addressing/credentials table; labeled **page 76** has the external Scale connection values. Obtain the assigned **Scale GUI / REST API username and password** there. The default username shown by v2.3 is `csi-storage-gui-user`.
4. Verify the intended **empty, disposable Ceph disk** on each of the three infrastructure nodes. `/dev/vde` is an example only.

> **Credential types are different:** `kubeadmin` is for OpenShift; `itzuser` plus the reservation's **Bastion Password** is for the existing Scale Linux VM's RDP login; `csi-storage-gui-user` plus its **Scale GUI password** is for the external Scale REST API. Do not paste any passwords or kubeconfig into GitHub. See [Scale troubleshooting](docs/LAB01-SCALE-TROUBLESHOOTING.md) for the VM access procedure.

## 4 — Validate your lab environment (read-only preflight check)

From the extracted Ubuntu installer directory, run:

```bash
bash install-lab01.sh plan \
  --cluster itz-REPLACE_ME \
  --kubeconfig "$HOME/.kube/REPLACE_ME.conf" \
  --scale-host REPLACE_WITH_EXISTING_SCALE_IP \
  --ceph-disk /dev/vde
```

Replace `itz-REPLACE_ME` with the **Environment ID**, `REPLACE_ME.conf` with your uploaded kubeconfig filename (for example `lab01.conf`), and the Scale placeholder with the VM's **IP Address**.

This checks OpenShift Container Platform (OCP) 4.21.x health, ClusterOperators, MachineConfigPools, and the planned stage sequence. It makes **no cluster changes**. Disk eligibility and external Scale access are checked at their respective deployment stages, **not** fully verified by the plan. Confirm the displayed target before proceeding.

## 5 — Deploy IBM Fusion Lab 1 (execute Ansible automation)

**This command actually installs and configures the supported Fusion/Ceph/Scale storage portion of Lab 1.** It can erase the selected Ceph disks and reboot worker nodes. Run it only against your disposable TechZone reservation, after reviewing the target and disks.

```bash
bash install-lab01.sh deploy \
  --cluster itz-REPLACE_ME \
  --kubeconfig "$HOME/.kube/REPLACE_ME.conf" \
  --scale-host REPLACE_WITH_EXISTING_SCALE_IP \
  --ceph-disk /dev/vde \
  --claim-disks \
  --allow-worker-reboots
```

**Then answer the two prompts:**

1. `Scale GUI username [csi-storage-gui-user]:` → press **Enter** for the displayed default, unless your lab gives another account.
2. `Scale GUI password (hidden):` → type the **Scale GUI password** from the lab guide and press **Enter**. No characters or asterisks will appear. Credentials are encrypted using **Ansible Vault** and stored outside the Git repository.

**Current behavior:** v2.3 asks for the password only **once** and does not authenticate to the remote Scale GUI before the long deployment. Password confirmation and early validation are future installer enhancements.

## 6 — Monitor the installation and confirm success

**Typical installation time: approximately 40 minutes in a healthy TechZone environment.** Actual duration depends on the reservation; worker reboots and API reconciliation can take time. Keep the Ubuntu SSH session connected and follow the displayed stages:

1. `fusion-ceph` — IBM Fusion and local Fusion Data Foundation/Ceph
2. `ceph-io-test` — Ceph persistent-volume I/O test
3. `scale-nodeprep` — IBM Storage Scale worker preparation
4. `scale-operator` — Scale Operator deployment
5. `scale-client` — Scale client deployment
6. `scale-external` — authentication, external `fs1` mount, StorageClass and I/O test
7. `final-verification` — read-only Fusion and Ceph health checks

At completion, look for:

```text
PASS: ALL LAB 01 INSTALLATION AND STORAGE TEST STAGES.
```

The supported scope is **installation and persistent storage**, not every exercise in the Fusion workbook. The external Scale test provisions a persistent volume, writes data, recreates the pod, remounts the volume, verifies SHA-256 integrity, and removes the test resources.

## 7 — If external Scale authentication fails

A `401 Unauthorized` or `403 Forbidden` from the remote Scale REST API may indicate wrong credentials or missing authorization. Don't repeatedly restart the entire installer. Consult [Scale troubleshooting and safe resume](docs/LAB01-SCALE-TROUBLESHOOTING.md). If the initial five stages passed and only `scale-external` failed, v2.3 supports `--update-scale-credentials --from scale-external` to replace encrypted credentials and resume without reinstalling Fusion/Ceph. **The v2.3 command still requires both `--claim-disks` and `--allow-worker-reboots` flags, even for a later-stage resume.**

## Validation status

**v2.3 passed a fresh TechZone OCP 4.21.24 end-to-end installation and persistence test on November 12, 2026, following a password correction and stage-level recovery.** The first attempt reached `scale-external` but failed after an authentication timeout. This is a validated recovery, **not** proof of an uninterrupted one-shot deployment. Read the [November 12 validation record](docs/07-LIVE-VALIDATION-2026-11-12.md) and [earlier validation record](VALIDATED-LAB01-RESULT.md).
