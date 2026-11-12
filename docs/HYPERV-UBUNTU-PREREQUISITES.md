# Hyper-V + Ubuntu automation VM prerequisites (Lab01)

This guide prepares a small Ubuntu **automation workstation** to run the IBM Fusion Lab01 Ansible automation. This VM **does not host** Red Hat OpenShift Container Platform (OCP) or IBM Fusion; it connects to an existing TechZone/OCP environment.

## 1. Windows host requirements

- A Windows edition supporting Microsoft Hyper-V, with hardware virtualization enabled.
- Hyper-V and Hyper-V Manager installed (via **Turn Windows features on or off**).
- Network connectivity from the Ubuntu VM to the target OCP application programming interface (API) and to any required package repositories.
- An Ubuntu Server 24.04 LTS **AMD64** installation ISO from [Ubuntu](https://ubuntu.com/download/server).

## 2. Suggested Hyper-V virtual machine configuration

| Setting | Value |
| --- | --- |
| Operating system | Ubuntu Server 24.04 LTS, 64-bit (AMD64) |
| Hyper-V generation | **Generation 2** |
| Processors | **2 virtual CPUs** |
| Memory | **4 GB startup**; Dynamic Memory on, **2 GB minimum / 8 GB maximum** |
| Virtual disk | **40 GB**, dynamically expanding **VHDX** |
| Network | **External virtual switch** with connectivity to the target environment |
| Secure Boot | **Enabled**, template **Microsoft UEFI Certificate Authority** |

These are convenient starting specifications for an automation controller, not sizing requirements for the OCP/Fusion cluster. Increase resources if the workload requires them.

## 3. Create and install the VM

1. Open **Hyper-V Manager** on Windows.
2. In **Virtual Switch Manager**, create or select an **External** switch that reaches your network.
3. Choose **New > Virtual Machine** and select **Generation 2**.
4. Configure the virtual CPUs, memory, VHDX, network, and Ubuntu Server ISO using the table above.
5. Before first boot, open **Settings > Security** and select **Microsoft UEFI Certificate Authority** as the Secure Boot template (not the Windows template).
6. Install Ubuntu Server. During installation, select **OpenSSH server** if offered.
7. Log in to the Ubuntu VM and update packages.

## 4. Install Ubuntu-side prerequisites

Run **inside Ubuntu** (not in Windows PowerShell):

```bash
sudo apt update
sudo apt install -y ansible python3 python3-pip python3-venv git curl unzip openssh-client openssh-server ca-certificates
sudo systemctl enable --now ssh
```

Check versions and determine the VM's IP address:

```bash
ansible --version
python3 --version
git --version
ip -br address
```

You may need extra Python libraries or Ansible collections for specific playbooks; follow the repository's version-specific requirements when specified. Avoid installing arbitrary Python packages system-wide with `sudo pip` on Ubuntu 24.04.

## 5. Install the OpenShift CLI (`oc`)

Download the matching **Linux AMD64 OpenShift command-line client** from the target cluster's **? > Command line tools** page (or its official OpenShift client download location). Transfer the tarball to Ubuntu and run:

```bash
tar -xzf openshift-client-linux*.tar.gz
sudo install -m 0755 oc /usr/local/bin/oc
oc version --client
```

If your downloaded filename differs, use that exact filename instead of the wildcard above. Install other required command-line tools only if the lab or playbooks need them.

## 6. Configure cluster access safely

Create the remote `.kube` directory in Ubuntu first, then copy your lab-specific kubeconfig into the VM using SecureCRT SFTP or another secure transfer tool. For example:

**Ubuntu SSH (run before transferring):**

```bash
mkdir -p "$HOME/.kube"
chmod 700 "$HOME/.kube"
```

**SecureCRT SFTP (Windows client):**

```text
lcd C:\Users\YOUR_USERNAME\Downloads
cd /home/automation/.kube
put lab01.conf
```

`YOUR_USERNAME` and `/home/automation` are examples; adjust them to your actual local and Linux user directories.

After transfer, run in Ubuntu:

```bash
chmod 600 "$HOME/.kube/lab01.conf"
export KUBECONFIG="$HOME/.kube/lab01.conf"
oc whoami
oc get nodes
```

**Never commit kubeconfig files, passwords, tokens, SSH keys, or other secrets to GitHub.**

## 7. Transfer the Lab01 release archive

Once the workstation is ready, transfer the **actual release ZIP filename** from your local download folder using SecureCRT SFTP. Example:

```text
lcd C:\Users\YOUR_USERNAME\Downloads
cd /home/automation
put IBM-Fusion-Lab01-OneCommand-v2.4.zip
```

Run the version-specific extraction and installation steps from this repository's Lab01 instructions. The ZIP filename above is a versioned **example**, not a promise that the latest release has that name.

## References

- [Ubuntu: Set up Ubuntu on Hyper-V](https://ubuntu.com/server/docs/how-to/virtualisation/ubuntu-on-hyper-v/)
- [Microsoft: Supported Ubuntu VMs on Hyper-V](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/supported-ubuntu-virtual-machines-on-hyper-v)
- [Microsoft: Create a virtual switch for Hyper-V VMs](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/get-started/create-a-virtual-switch-for-hyper-v-virtual-machines)
