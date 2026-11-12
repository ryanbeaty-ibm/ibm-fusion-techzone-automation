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

**Recommended for new users:** open the repository's [Releases page](https://github.com/ryanbeaty-ibm/ibm-fusion-techzone-automation/releases). Under the appropriate release, download the attached installer file, for example `IBM-Fusion-Lab01-OneCommand-v2.3.zip`.

**Important:** a GitHub *release asset* (the maintainer-uploaded installer ZIP) is different from the automatic source archive under **Code → Download ZIP**. The latter downloads repository source and is **not necessarily** the tested one-command release package. If the expected ZIP is not listed under Releases, ask the repository maintainer to publish it before following the ZIP-based installer steps.

**Current validation note:** the v2.3 package is described in this repository as a cleanup candidate; v2.2 is the preceding fresh-cluster, end-to-end validated release. Check the release description and [validation record](../VALIDATED-LAB01-RESULT.md) for the package you choose.

## 3. Make a fresh TechZone reservation

Reserve the environment required by the Lab 1 workbook (the project currently targets OCP 4.21.x). Record:

- Your TechZone reservation's OCP API endpoint and fresh kubeconfig.
- The existing external IBM Storage Scale server's address and required credentials.
- The **disposable** disk device assigned for Ceph storage on **each** of the three infrastructure nodes.

Use a newly downloaded kubeconfig for the current reservation. Never commit kubeconfig files, passwords, tokens, private keys, or other lab credentials to Git.

## 4. Configure Secure Shell (SSH) and upload the kubeconfig

Connect to the Ubuntu VM from Windows using an SSH client (SecureCRT is the documented example). In SecureCRT SFTP, use `lcd` to select the directory on your Windows computer containing the kubeconfig. The exact Windows directory is your choice.

On the Ubuntu host, first create a protected Kubernetes configuration directory:

```bash
mkdir -p "$HOME/.kube" && chmod 700 "$HOME/.kube"
```

Transfer the downloaded kubeconfig with SecureCRT SFTP and save it as `$HOME/.kube/lab01.conf`. Restrict access and test it on Ubuntu:

```bash
chmod 600 "$HOME/.kube/lab01.conf"
oc --kubeconfig="$HOME/.kube/lab01.conf" whoami
oc --kubeconfig="$HOME/.kube/lab01.conf" get nodes
```

For the tested SecureCRT file-transfer procedure and exact steps, continue in [Start here — Lab 1 installer](../README-START-HERE.md). That file assumes this Ubuntu setup is now finished.

## 5. Transfer the installer ZIP and run the read-only plan

Follow the instructions in [README-START-HERE.md](../README-START-HERE.md) to transfer and unpack the **downloaded release ZIP** into a new versioned directory on Ubuntu (do not overwrite an earlier validated workspace). Run the read-only `plan` first, examine the selected cluster, external Storage Scale endpoint, and storage devices, and confirm the environment is healthy.

## 6. Deploy only after reviewing the plan

Run the installer `deploy` only when you have positively identified the **intentionally disposable Ceph disks** and are authorized to make changes to your disposable TechZone reservation. Deploy can erase those disks and may reboot cluster nodes. Follow the post-install validation steps in [README-START-HERE.md](../README-START-HERE.md) and review the [live validation record](../VALIDATED-LAB01-RESULT.md).

## Experienced Ansible user?

You can skip Ubuntu/Hyper-V setup if you already have a compatible Ansible control node with Python, `oc`, SSH access, and a fresh kubeconfig. Go directly to [Start here — Lab 1 installer](../README-START-HERE.md).
