# Prepare two IBM TechZone environments and an Ubuntu automation VM

> **First time doing this lab?** Follow the numbered [Lab 02 installation walkthrough](LAB02-BACKUP-AND-RESTORE.md) first. This page is an additional technical prerequisites reference.

## Reserve both clusters before beginning

The complete IBM Fusion Level 4 Lab 02 requires **two independent OpenShift clusters, normally two separate TechZone reservations**, running concurrently. Earlier hub backup/restore work needs one cluster; **spoke onboarding and cross-cluster restore require both**. Reuse an existing second cluster only if it meets the version, storage, networking and permissions requirements. A participant does **not** have to perform Lab 01 to run Lab 02; our team happened to reuse the completed Lab 01 cluster as the Lab 02 spoke.

Assign one reservation as **Hub** (Backup & Restore control plane), one as **Spoke** (agent only). Ensure both have IBM Fusion installed at compatible versions (tested 2.14.1) and OpenShift Container Platform (OCP) (tested 4.21.24). Keep the hub and spoke reservation credentials out of the repository.

## Ubuntu / Ansible baseline

Example Ubuntu commands (verify package names against your installed Ubuntu release):

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv ansible openssl curl unzip git jq
# Install the Red Hat/OpenShift CLI (oc) suitable for your OCP version by an approved method.
# Validate:
python3 --version
ansible-playbook --version
oc version --client
openssl version
```

Install `oc` following Red Hat OpenShift guidance or from your TechZone console. Do not place a downloaded `oc` binary or kubeconfig in the Git repository. Required Ansible collections are built-in for the supplied playbooks (`ansible.builtin`).

## Kubeconfigs and identities

Save separate kubeconfigs under `~/.kube` with permissions `600`, e.g.:

```bash
mkdir -p ~/.kube
chmod 700 ~/.kube
chmod 600 ~/.kube/lab02.conf ~/.kube/lab01.conf
oc --kubeconfig="$HOME/.kube/lab02.conf" whoami --show-server
oc --kubeconfig="$HOME/.kube/lab01.conf" whoami --show-server
```

Hub and spoke API endpoints must be different. Fill `config/environment.yml` using `config/environment.example.yml`. The example hostnames are *only* the validated TechZone example; participants MUST enter their own reservation hostnames. For the registered spoke's `spoke_cluster_name`, use `oc --kubeconfig=<hub-conf> get cluster -A` **after** onboarding; the value is the exact `Cluster.metadata.name` (usually the spoke apps domain), not the API URL. Do not confuse the spoke's kubeconfig path with the hub's.

## Storage prerequisites

On hub, verify:

```bash
oc --kubeconfig="$HOME/.kube/lab02.conf" get sc ocs-storagecluster-ceph-rbd
oc --kubeconfig="$HOME/.kube/lab02.conf" get volumesnapshotclass ocs-storagecluster-rbdplugin-snapclass
oc --kubeconfig="$HOME/.kube/lab02.conf" get sc openshift-storage.noobaa.io
```

On spoke, verify:

```bash
oc --kubeconfig="$HOME/.kube/lab01.conf" get sc ocs-storagecluster-ceph-rbd
```

The hub must have a working external HTTPS route for NooBaa S3, and spoke pods must reach it. Test reachability from a pod **inside the spoke**, not just from Ubuntu; unauthenticated HTTP `403` indicates endpoint reachability only, not valid credentials. Spoke agent also requires hub Kafka bootstrap/broker/bridge connectivity; the bootstrap process and Fusion Topology verify its establishment. The Fusion UI's automated-deployment form in our version requests snapshot-capable **ReadWriteOnce** storage and at least **34 GiB** available for the spoke agent.

## Security and privileges

The lab requires permissions to create namespaces, Fusion custom resources, deployments, services, secrets, OBCs, PVCs and an SCC grant for the temporary MongoDB ownership repair Job. The automation refuses unexpected cluster identities and some unmanaged pre-existing resources. Avoid deploying into production clusters.

Service Protection's S3 destination must remain available independently if the hub fails. Using NooBaa on the spoke suffices for our controlled two-cluster demonstration; consider object storage lifecycle, credentials, and a separate failure domain for real systems.
