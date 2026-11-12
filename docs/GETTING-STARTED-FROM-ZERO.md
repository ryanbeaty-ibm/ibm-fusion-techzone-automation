# Getting Started from Zero — IBM Fusion Lab 1

This guide is for IBM engineers who have a Windows computer and an IBM TechZone reservation but **do not yet have an Ansible control node**. You do not install IBM Fusion or Red Hat OpenShift Container Platform (OCP) inside your automation virtual machine (VM): the VM connects to the existing TechZone environment and orchestrates its configuration.

> **Lab / disposable environment only.** Lab 1 can claim and erase the disks selected for Ceph storage, and may reboot infrastructure nodes. Never use this workflow against production infrastructure.

## 1. Prepare an Ubuntu automation VM (or reuse an existing one)

**New to Ansible? Start here:** follow [Hyper-V + Ubuntu prerequisites](HYPERV-UBUNTU-PREREQUISITES.md) for an example using Windows Hyper-V and Ubuntu Server 24.04 LTS. Other hypervisors and an existing compatible Ubuntu server are fine; Hyper-V is only the documented example.

On the Ubuntu automation host, confirm the required tools are installed:

```bash
python3 --version
ansible --version
git --version
oc version --client
ssh -V
```

If a command is missing, return to the [prerequisites guide](HYPERV-UBUNTU-PREREQUISITES.md). You also need network access to the TechZone OCP API and any other required lab endpoints.

## 2. Download the Lab 1 installer

**Recommended for new users:** open the repository's [Releases page](https://github.com/ryanbeaty-ibm/ibm-fusion-techzone-automation/releases). Under the appropriate release, download the attached installer file, for example `IBM-Fusion-Lab01-OneCommand-v2.4.zip`.

**Important:** a GitHub *release asset* (the maintainer-uploaded installer ZIP) is different from the automatic source archive under **Code → Download ZIP**. The latter downloads repository source and is **not necessarily** the tested one-command release package. If the expected ZIP is not listed under Releases, ask the repository maintainer to publish it before following the ZIP-based installer steps.

**Version note:** The v2.4 installer is an **unvalidated pre-release** with offline tests passing; v2.3 remains the live-validated baseline.

**Validation update (November 12, 2026):** the published v2.3 installer passed a fresh-cluster OCP 4.21.24 end-to-end installation and storage validation **after correcting the Scale GUI password and resuming the failed stage**. It did not succeed as an uninterrupted first attempt. See [v2.3 live validation](07-LIVE-VALIDATION-2026-11-12.md); the earlier [v2.2 record](../VALIDATED-LAB01-RESULT.md) is retained.

## 3. Make a fresh TechZone reservation

<!-- LAB01 RESERVATION SETTINGS BEGIN -->
For **IBM Fusion Level 4 training** (not just Lab 1), choose **IBM Fusion on OpenShift Virtualization**. In the request wizard, open **Step 5 — Configuration** and use these values. Earlier trials with 8-vCPU/32-GB workers left insufficient CPU and memory headroom for Fusion and storage workloads:

| Configuration setting | Selection |
| --- | --- |
| OpenShift Cluster Version | **4.21** |
| Worker Node Count | **3** |
| Worker Node Flavor | **16 vCPU / 64 GB RAM / 300 GB ephemeral storage** |
| VM Network CIDR | `10.10.10.0/24` (default) |
| OCP/Kubernetes Cluster Network | `10.128.0.0/14` (default) |
| OCP/Kubernetes Service Network | `172.30.0.0/16` (default) |

The reservation provides the three control-plane and three infrastructure nodes for the nine-node Level 4 training topology. Keep the displayed network defaults. This is a recommended training baseline, not production sizing, and other exercises may need more capacity. The 300-GB ephemeral disk does not replace the separate disposable Ceph disk required by Lab 1.
<!-- LAB01 RESERVATION SETTINGS END -->

Reserve the environment required by the Lab 1 workbook (the project currently targets OCP 4.21.x). Record:

- Your TechZone reservation's OCP API endpoint and fresh kubeconfig.
- The existing external IBM Storage Scale server's address and required credentials.
- The **disposable** disk device assigned for Ceph storage on **each** of the three infrastructure nodes.

Find the **Environment ID** in reservation Outputs, the existing `xxx-scale-2` VM **IP address** under VM Remote Console, and the **Scale GUI username/password** in the IBM Fusion lab guide (labeled pages **30 and 76**). The GUI credentials are different from the VM login credentials. Use a newly downloaded kubeconfig for the current reservation. Never commit kubeconfig files, passwords, tokens, private keys, or other lab credentials to Git.

## 4. Configure Secure Shell (SSH) and upload the kubeconfig

Connect to the Ubuntu VM from Windows using an SSH client (SecureCRT is the documented example). In SecureCRT SFTP, use `lcd` to select the directory on your Windows computer containing the kubeconfig. The exact Windows directory is your choice.

On the Ubuntu host, first create a protected Kubernetes configuration directory:

```bash
mkdir -p "$HOME/.kube" && chmod 700 "$HOME/.kube"
```

Download the kubeconfig from reservation **Download kubeconfig**; save it locally as `lab01.conf` in `C:\Users\YOUR_USERNAME\Downloads`. Transfer with SecureCRT SFTP using `lcd C:\Users\YOUR_USERNAME\Downloads`, `cd /home/automation/.kube`, and `put lab01.conf`. Save it as `$HOME/.kube/lab01.conf`. Restrict access and test it on Ubuntu:

```bash
chmod 600 "$HOME/.kube/lab01.conf"
oc --kubeconfig="$HOME/.kube/lab01.conf" whoami
oc --kubeconfig="$HOME/.kube/lab01.conf" get nodes
```

For the tested SecureCRT file-transfer procedure and exact steps, continue in [Start here — Lab 1 installer](LAB01-INSTALLATION-AND-CONFIGURATION.md). That guide assumes this Ubuntu setup is now finished.

## 5. Transfer the installer ZIP and run the read-only plan

Follow the instructions in [README-START-HERE.md](LAB01-INSTALLATION-AND-CONFIGURATION.md) to transfer and unpack the **downloaded release ZIP** into a new versioned directory on Ubuntu (do not overwrite an earlier validated workspace). Run the read-only `plan` first, examine the selected cluster, external Storage Scale endpoint, and storage devices, and confirm the environment is healthy. The `plan` does **not** change cluster resources; it also does not yet validate the external Scale GUI password.

## 6. Deploy only after reviewing the plan

Run the installer `deploy` only when you have positively identified the **intentionally disposable Ceph disks** and are authorized to make changes to your disposable TechZone reservation. Deploy can erase those disks and may reboot cluster nodes. Expect roughly **40 minutes** in a healthy lab. The deploy command prompts for the **Scale GUI username** (press Enter to accept `csi-storage-gui-user`) and the **hidden Scale GUI password twice** (confirmation required). New or updated credentials receive an early read-only API test from an OpenShift worker. Follow the post-install validation steps in [README-START-HERE.md](LAB01-INSTALLATION-AND-CONFIGURATION.md), and see the [Scale troubleshooting/resume guide](LAB01-SCALE-TROUBLESHOOTING.md) if authentication fails. Review the [November 12 v2.3 validation record](07-LIVE-VALIDATION-2026-11-12.md).

## Experienced Ansible user?

You can skip Ubuntu/Hyper-V setup if you already have a compatible Ansible control node with Python, `oc`, SSH access, and a fresh kubeconfig. Go directly to [Start here — Lab 1 installer](LAB01-INSTALLATION-AND-CONFIGURATION.md).
