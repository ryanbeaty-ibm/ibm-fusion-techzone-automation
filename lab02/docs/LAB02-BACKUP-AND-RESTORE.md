# Lab 02 — Backup and Restore: step-by-step installation guide

**Audience:** Someone beginning the IBM Fusion Level 4 Backup and Restore lab with two IBM TechZone reservations and an Ubuntu VM. This guide is intentionally written as a **walkthrough**: do Step 1, then Step 2, and so on. You run **one Ansible command** for the actual lab, with two manual IBM Fusion UI checkpoints.

[Back to Lab 02 overview](../README.md) · [Lab 02 troubleshooting](troubleshooting.md)

## Step 1 — Reserve your two IBM Fusion environments

1. Sign in to **IBM Technology Zone (TechZone)** with the access required for the IBM Fusion Level 4 hands-on environments.
2. Provision **two separate** eligible Red Hat OpenShift Container Platform (OCP) clusters with IBM Fusion preinstalled or installed as part of the provided environment. Call them **Hub** and **Spoke**. Keep both reservations active until you finish Step 9.
3. Note the OpenShift console URL, API server URL and administrative login or kubeconfig for **each** cluster. They must be different clusters.
4. Confirm that each cluster has suitable OpenShift Data Foundation (ODF) / Ceph Block storage. The hub also needs snapshot support and NooBaa object storage.

**Our tested example (November 2026):** Hub `itz-t63twk`, spoke `itz-2xvmb0`, both OCP **4.21.24** and IBM Fusion **2.14.1**. We reused a previously deployed Lab 01 cluster as the spoke, but **you do not need to run Lab 01 to complete Lab 02**. Do **not** install a second full Backup & Restore hub on the spoke; the automation installs its **agent** later.

**Expected result:** You have two working OpenShift consoles and two sets of administrator credentials. They are available simultaneously.

## Step 2 — Prepare your Ubuntu automation VM

1. Create or reuse an **Ubuntu Linux VM** that can reach the API endpoints of **both** reservations. This VM is the Ansible control node; you do not install Ansible inside the OpenShift clusters.
2. Open the Ubuntu terminal and install the base tools:

   ```bash
   sudo apt-get update
   sudo apt-get install -y python3 python3-pip python3-venv ansible git curl unzip jq openssl
   ```

3. Install the **OpenShift CLI (`oc`)** appropriate for your OpenShift release. From either OpenShift console, open the **Help / Command line tools** download area, download the Linux CLI and install it according to the Red Hat guidance for your machine. The installer does **not** download `oc` for you.
4. Verify the tools:

   ```bash
   python3 --version
   ansible-playbook --version
   oc version --client
   openssl version
   git --version
   ```

**Expected result:** Each command returns a version. If `oc` is not found, fix your CLI installation and `PATH` before continuing. Avoid installing optional packages unrelated to this lab.

## Step 3 — Put both cluster kubeconfigs on Ubuntu

You need **two separate** Kubernetes client configuration files (kubeconfigs), one for each cluster. Obtain them securely from your TechZone reservation or OpenShift administrator. If you're using the OpenShift web console to log in, follow its **Copy login command** instructions; then save the authenticated context as a dedicated kubeconfig rather than overwriting your other cluster's context.

1. Make a protected kubeconfig directory:

   ```bash
   mkdir -p "$HOME/.kube"
   chmod 700 "$HOME/.kube"
   ```

2. Store the **hub** file at `~/.kube/lab02.conf` and the **spoke** file at `~/.kube/lab01.conf`. These are our examples; you can use your own paths and update the configuration in Step 5. Do not put these files in the GitHub repository.

   **Don't already have kubeconfig files?** If your TechZone reservation provides a `kubeadmin` login, you can create each kubeconfig from Ubuntu using `oc login`. Replace the two API addresses with the ones shown in **your** reservations. The CLI prompts for the password; **do not paste passwords into commands or GitHub**:

   ```bash
   oc login --kubeconfig="$HOME/.kube/lab02.conf" \
     --server=https://api.YOUR_HUB_CLUSTER:6443 --username=kubeadmin

   oc login --kubeconfig="$HOME/.kube/lab01.conf" \
     --server=https://api.YOUR_SPOKE_CLUSTER:6443 --username=kubeadmin
   ```

   If your environment authenticates differently, use that OpenShift console's **Copy login command** flow, applying the correct `--kubeconfig` path for each cluster. Follow your organization's certificate-authority instructions; don't disable TLS verification merely to get past a certificate error.

3. Protect the files and verify both targets:

   ```bash
   chmod 600 "$HOME/.kube/lab02.conf" "$HOME/.kube/lab01.conf"

   echo '=== Hub ==='
   oc --kubeconfig="$HOME/.kube/lab02.conf" whoami --show-server

   echo '=== Spoke ==='
   oc --kubeconfig="$HOME/.kube/lab01.conf" whoami --show-server
   ```

**Expected result:** Two **different** `https://api....:6443` API endpoints. If the endpoints are identical, stop: you have accidentally configured the same cluster twice. Check that the credentials have privileges to create Fusion service instances, namespaces, Secrets, PVCs, snapshots, S3 bucket claims and applications.

## Step 4 — Clone the repository

From the Ubuntu terminal:

```bash
cd "$HOME"
git clone https://github.com/ryanbeaty-ibm/ibm-fusion-techzone-automation.git
cd ibm-fusion-techzone-automation/lab02
```

If you cloned the repository previously, instead run:

```bash
cd "$HOME/ibm-fusion-techzone-automation/lab02"
```

Check that you are in the right directory:

```bash
ls README.md scripts/run-lab02.sh config/environment.example.yml
```

**Expected result:** All three files exist. Do not run the Lab 01 installer; Lab 02 has its own entry point.

## Step 5 — Configure your hub and spoke

The sample `environment.example.yml` contains names from our **old** TechZone reservation. They are **examples, not universal values**. Create an ignored private configuration file:

```bash
cp config/environment.example.yml config/environment.yml
chmod 600 config/environment.yml
nano config/environment.yml
```

Use **your** values for these entries:

| Configuration entry | What to enter |
|---|---|
| `hub_kubeconfig`, `lab02_kubeconfig` | Absolute path to your **hub** kubeconfig |
| `spoke_kubeconfig` | Absolute path to your **spoke** kubeconfig |
| `hub_api_fragment`, `expected_hub_api_fragment` | Hostname from the **hub** `oc whoami --show-server` result (without `https://` or port) |
| `spoke_api_fragment` | Hostname from the **spoke** `oc whoami --show-server` result |
| `expected_hub_s3_route_prefix` | Beginning of your **hub** S3 route hostname, for example `s3-openshift-storage.apps.<hub-cluster>.` |
| `service_protection_s3_route` | Full S3 route hostname of the **spoke** cluster; do not include `https://` |
| `spoke_cluster_name` | Spoke **apps domain** used by the Fusion Topology registration (not the spoke API address) |

Find the two S3 route hostnames with:

```bash
oc --kubeconfig="$HOME/.kube/lab02.conf" \
  -n openshift-storage get route s3 -o jsonpath='{.spec.host}{"\n"}'

oc --kubeconfig="$HOME/.kube/lab01.conf" \
  -n openshift-storage get route s3 -o jsonpath='{.spec.host}{"\n"}'
```

To see the spoke apps domain before connecting the spoke:

```bash
oc --kubeconfig="$HOME/.kube/lab01.conf" \
  get ingress.config.openshift.io cluster -o jsonpath='{.spec.domain}{"\n"}'
```

After the spoke is connected, you can confirm the exact `spoke_cluster_name` registered on the hub with `oc --kubeconfig="$HOME/.kube/lab02.conf" get cluster -A`. The named `Cluster` resources are **namespaced**, so `-A` matters.

**Important:** Use only harmless hostnames and local file **paths** in `environment.yml`. Do not paste OBC passwords, authentication tokens, kubeconfig contents or private keys. This file is in `.gitignore`.

**Expected result:** The correct two OpenShift API endpoints and S3 routes are set for your reservations.

## Step 6 — Start the automated lab

From the `lab02` directory:

```bash
bash scripts/run-lab02.sh --plan
bash scripts/run-lab02.sh
```

The first command **displays the plan** without modifying any cluster. The second begins the actual automation. It runs these tasks in sequence without asking you to issue separate playbook commands:

| Automated work | What you should see |
|---|---|
| Stage **01** — Install hub Backup & Restore service | Fusion hub service instance `Completed` |
| Stage **02** — Create S3 bucket, location and backup policies | Location `hubspoke-bucket` `Connected` |
| Stage **03** — Deploy and recover FileBrowser | Backup and restore complete; 8 MiB SHA-256 data proof matches |
| Stage **04** — MongoDB/Pac-Man consistent backup and recovery | Consistency recipe and restored document verification pass |
| Stage **05a** — Prepare Service Protection S3 on second cluster | Dedicated Object Bucket Claim (OBC) bound, certificate Secret created |

Stage 05a outputs the **non-secret S3 endpoint and generated bucket name** to help with Step 7. For the two credential fields, use the OBC Secret on the **spoke**, not any key from the hub's main application-backup bucket.

**Expected result:** Automation reaches the first manual checkpoint **05b**. Don't close the Ubuntu session; leave it at the `CONTINUE` prompt while you use the IBM Fusion web interface.

## Step 7 — Manual checkpoint 1: Service Protection in Fusion UI (05b)

This is a **Fusion GUI task**. Ansible already created the supporting S3 bucket and certificate; you are only configuring IBM Fusion to use them.

1. In a browser, open **IBM Fusion on the HUB cluster**. (Do not perform this UI step on the spoke.)
2. On the left, open **Backup & restore → Service protection**.
3. Select **Configure service backups**. Choose **S3 Compliant**, then **Next**.
4. Enter the S3 endpoint and **generated bucket name** from stage 05a. Use the credential values from the Secret named `lab02-service-protection` in the **spoke** namespace `fusion-lab02-protection` (fields `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`). You can access that Secret through the spoke OpenShift console. **Never paste credentials into chat, screenshots, the README or GitHub.**
5. Specify the hub certificate Secret `lab02-service-protection-cert`, then select **Add**. Confirm the storage location reports **Connected**.
6. Select **Define schedule**. For our validation we used **Daily**, a **12:00 AM–4:00 AM** window, timezone **America/Los_Angeles**, **30 days** retention and **Initiate Service backup now** enabled. Set equivalent values appropriate to your reservation.
7. Select **Create policy**. Watch the Service Protection page until the first service backup reports **Completed** (not merely scheduled). Confirm the location is still **Connected**.
8. Return to Ubuntu and type exactly `CONTINUE` at the paused runner prompt.

Ansible then performs automated stage **05c** to recheck the bucket, certificate and endpoint. **05c does not prove a Service Protection backup completed**; that status must be observed in Fusion in step 7 above.

**Expected result:** Service Protection location **Connected**, at least one backup **Completed**; automation proceeds to the second checkpoint **06a**.

For additional UI detail or troubleshooting, see [Service Protection checkpoint instructions](manual-checkpoints.md#v05--service-protection-ui-configuration-is-required).

## Step 8 — Manual checkpoint 2: connect the spoke (06a)

This checkpoint generates a **short-lived connection manifest in the hub UI**. Ansible applies it to the **spoke**; do not apply it to the hub.

1. On the **hub** IBM Fusion UI, go to **Backup & restore → Topology**.
2. Select **Connect cluster → Automate deployment**.
3. In the storage field, enter your spoke's snapshot-capable StorageClass (our tested cluster used `ocs-storagecluster-ceph-rbd`). The UI may specify at least **34 GiB** ReadWriteOnce storage for the agent.
4. Select **Generate → Deploy using YAML → Download YAML**. The downloaded filename is `BackupAndRestoreAgentDeployment.yaml`.
5. Copy the downloaded YAML to your **Ubuntu automation VM's home directory**, not to your GitHub project folder. Example from **Windows PowerShell**, replacing the local path and Ubuntu host with yours:

   ```powershell
   scp "D:\Downloads\BackupAndRestoreAgentDeployment.yaml" automation@YOUR_UBUNTU_HOST:~/BackupAndRestoreAgentDeployment.yaml
   ```

6. Back in **Ubuntu**, protect the YAML and verify only that it exists (do not print its contents):

   ```bash
   chmod 600 "$HOME/BackupAndRestoreAgentDeployment.yaml"
   test -s "$HOME/BackupAndRestoreAgentDeployment.yaml" && echo 'Spoke manifest ready'
   ```

7. Return to the paused runner and type exactly `CONTINUE`. Ansible uses the **spoke kubeconfig** to validate and apply the YAML and waits for the service instance to report **Completed**.
8. Open **hub Fusion → Backup & restore → Topology** again. Confirm **two clusters**: Hub **Healthy** and Spoke **Connected / Healthy**.

**Security:** This YAML contains an authentication token with an approximately **one-hour** lifetime. If it expires before installation, generate another one in the hub UI. **Never put the YAML, Secret contents or kubeconfigs in Git.** If the spoke agent is already installed and healthy, the automation can reuse it; you don't need to regenerate a manifest.

**Expected result:** Spoke Fusion agent deployed and hub Topology **Connected / Healthy**. The same runner starts automated stage **07** without further UI work.

## Step 9 — Verify cross-cluster restore and data integrity (07)

The runner restores the hub's FileBrowser S3 backup to the **spoke**, confirms the FileBrowser Deployment and both persistent volumes are ready and compares the original file's SHA-256 checksum with the recovered copy. The runner finishes with:

```text
===== LAB 02 COMPLETE =====
```

Check the live objects from Ubuntu:

```bash
HUB="$HOME/.kube/lab02.conf"
SPOKE="$HOME/.kube/lab01.conf"

echo '=== Hub: completed cross-cluster restore ==='
oc --kubeconfig="$HUB" -n ibm-spectrum-fusion-ns \
  get frestore filebrowser-lab02-v07-restore

echo '=== Spoke: recovered application and persistent volumes ==='
oc --kubeconfig="$SPOKE" -n filebrowser get deployment,pods,pvc
```

**Expected result:** Restore **Completed**; FileBrowser pod **Running**; the `files` and `filebrowser-config` Persistent Volume Claims **Bound**. The runner itself compares the recovered content with the source. To verify the 8 MiB test file again, rerun the non-destructive stage 07 verifier:

```bash
bash scripts/run-stage.sh 07 run
```

On our November 2026 test, both clusters produced the same SHA-256:

```text
caf85e4ede776f0a8ab82bae96ae0ec126f8ce8f3fb8ff6c0dcc8c585a2d608b
```

That hash is **evidence from our tested data**, not a required value for every new reservation. A new test may generate different data. What matters is that the **two hashes match**.

## If something fails — do not start over blindly

The runner stops at the failure. Fix the issue, then resume with `--from` and the affected stage:

```bash
# Examples — choose ONE matching your situation:
bash scripts/run-lab02.sh --from 02
bash scripts/run-lab02.sh --from 05b
bash scripts/run-lab02.sh --from 06a
bash scripts/run-lab02.sh --from 07
```

Use the [troubleshooting guide](troubleshooting.md) for diagnostics, or [advanced stage commands](advanced-operations.md) when you specifically need one playbook. Avoid deleting completed backups, application data or namespaces to make reruns seem clean. Existing data is intentionally preserved.

## What is automated, what is not?

- **Automatic:** stages 01, 02, 03, 04, 05a, 05c, 06b and 07 (when run through the unified runner).
- **Manual:** stage 05b **Fusion Service Protection GUI**, and stage 06a **Fusion hub-generated agent YAML**. These are both checkpoint pauses inside the same command.

**Implementation status:** The underlying v0.1–v0.4.4 workflows and cross-cluster recovery were live validated separately. The consolidated one-command runner and the new automatic 05a/05c/06b helpers have undergone static checks, **not a fresh end-to-end live run**. The first cross-cluster Restore custom resource was created via `oc` and adopted/verified by the v0.7 Ansible playbook (`ok=21 changed=0 failed=0`). See [the evidence record](../evidence/validated-runs.md). No full Backup & Restore control-plane disaster recovery was attempted.

**Safety:** This is an educational automation lab, not a production recovery guarantee. The sample MongoDB application is intentionally unsecured for the lab. Use a dedicated nonproduction environment and follow [security guidance](security.md). Do not redistribute the original proprietary IBM workbook in this repository.
