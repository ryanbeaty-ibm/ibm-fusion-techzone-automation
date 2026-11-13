# Lab 02 GitHub documentation — manual checkpoints between Ansible stages

> **Start here instead for first-time setup:** [Lab 02 step-by-step walkthrough](LAB02-BACKUP-AND-RESTORE.md). The two manual checkpoints below are part of the **one-command** guided run, not separate installation scripts.

These instructions reflect the validated lab workflow through November 13, 2026. Screens and labels may vary with the installed IBM Fusion version. Never publish a generated deployment Secret, service credentials, kubeconfig, or access tokens.

## Before starting

Provision **two separate OpenShift/Fusion clusters** (normally two TechZone reservations), one hub and one spoke. They must remain available concurrently for the late Lab 02 exercises. Our validated example reused the cluster from Lab 01 for the spoke, so a new reservation was unnecessary in this specific environment. The Lab 01 **automation workspace was not modified**.

- Hub: `itz-t63twk`, OCP 4.21.24, Fusion 2.14.1, kubeconfig `~/.kube/lab02.conf`
- Spoke: `itz-2xvmb0`, OCP 4.21.24, Fusion 2.14.1, kubeconfig `~/.kube/lab01.conf`

### Automated stages before this manual interlude

- v0.1: install hub service
- v0.2: NooBaa S3 location and policies
- v0.3: FileBrowser S3 backup, alternate-namespace restore, SHA-256 proof
- v0.4.4: MongoDB application-consistent backup, alternate namespace restore, UID ownership repair, SHA-256 proof

## v0.5 — Service Protection (UI configuration is required)

**Automated stage 05a (`./scripts/run-lab02.sh`)**: On a second cluster (our spoke), create dedicated namespace `fusion-lab02-protection` and a NooBaa Object Bucket Claim (OBC) `lab02-service-protection`. Verify OBC is `Bound`. The bucket name is generated per reservation; never hard-code the sample name as a general prerequisite. Get the generated S3 endpoint and the OBC `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` from the Kubernetes Secret **without printing or committing them**. From a pod inside the hub's `ibm-backup-restore` namespace, verify HTTPS reachability to this second-cluster S3 route. The unauthenticated HTTP `403` confirms an endpoint responds but does not verify credential permissions. Create the remote S3 TLS certificate Secret `lab02-service-protection-cert` in the hub `ibm-spectrum-fusion-ns` namespace. Ensure the PEM has a real trailing newline. In the validated run, external route HTTPS certificate validation succeeded.

### Legacy manual preparation commands (optional troubleshooting; normally stage 05a runs automatically)

From the Ubuntu automation VM, customize the kubeconfig paths and run these commands **before** the GUI work. They were exercised against the two TechZone clusters in the validated run:

```bash
SPOKE="$HOME/.kube/lab01.conf"
HUB="$HOME/.kube/lab02.conf"
OBC_NS=fusion-lab02-protection
OBC=lab02-service-protection

# Always check the target cluster first.
oc --kubeconfig="$SPOKE" whoami --show-server
oc --kubeconfig="$HUB" whoami --show-server

oc --kubeconfig="$SPOKE" create namespace "$OBC_NS" \
  --dry-run=client -o yaml | oc --kubeconfig="$SPOKE" apply -f -
cat <<'EOF' | oc --kubeconfig="$SPOKE" apply -f -
apiVersion: objectbucket.io/v1alpha1
kind: ObjectBucketClaim
metadata:
  name: lab02-service-protection
  namespace: fusion-lab02-protection
  labels:
    app.kubernetes.io/managed-by: lab02-ansible
    app.kubernetes.io/part-of: fusion-lab02
spec:
  generateBucketName: lab02-service-protection
  storageClassName: openshift-storage.noobaa.io
EOF
oc --kubeconfig="$SPOKE" -n "$OBC_NS" wait \
  --for=jsonpath='{.status.phase}'=Bound "obc/$OBC" --timeout=180s

# Bucket name is not secret; its *generated* value varies by reservation.
oc --kubeconfig="$SPOKE" -n "$OBC_NS" get configmap "$OBC" \
  -o jsonpath='{.data.BUCKET_NAME}{"\n"}'
# Confirm existence, do not print Secret data:
oc --kubeconfig="$SPOKE" -n "$OBC_NS" get secret "$OBC" -o name
```

Get the **second-cluster** S3 route hostname using `oc --kubeconfig="$SPOKE" -n openshift-storage get route s3 -o jsonpath='{.spec.host}'`. From **inside the hub** `ibm-backup-restore` namespace, launch a short-lived `curlimages/curl` pod with a `curl -sS https://<spoke-s3-route>` probe. A `403` from unauthenticated S3 is enough for network connectivity, but not permission verification. The exact validated test is described in the step-by-step chat record; use your own route.

For the certificate Secret, the following **lab-only** pattern retrieves the public TLS leaf certificate and stores it in the hub. A server certificate is not a private key. Verify the certificate matches the route hostname and trust requirements. The temporary file is removed afterward.

```bash
HUB="$HOME/.kube/lab02.conf"
S3_HOST=$(oc --kubeconfig="$HOME/.kube/lab01.conf" -n openshift-storage get route s3 -o jsonpath='{.spec.host}')
(
  set -e
  TMP=$(mktemp -d)
  trap 'rm -rf "$TMP"' EXIT
  openssl s_client -connect "$S3_HOST:443" -servername "$S3_HOST" \
    -showcerts </dev/null 2>/dev/null | \
    sed -n '/-----BEGIN CERTIFICATE-----/,/-----END CERTIFICATE-----/p' > "$TMP/tls.crt"
  openssl x509 -in "$TMP/tls.crt" -noout -dates -ext subjectAltName
  oc --kubeconfig="$HUB" -n ibm-spectrum-fusion-ns \
    create secret generic lab02-service-protection-cert --type=Opaque \
    --from-file=tls.crt="$TMP/tls.crt" --dry-run=client -o yaml | \
    oc --kubeconfig="$HUB" -n ibm-spectrum-fusion-ns apply -f -
)
```

Note: this copies a public server certificate (not its signing CA). Our validated TechZone setup accepted it; for environments that require a private trust anchor, use the issuer CA certificate as IBM documentation specifies. Do not enable `-k` certificate bypass in the final application configuration.

**Manual IBM Fusion hub UI**:

1. Open **Backup & restore → Service protection** on the HUB (not the spoke).
2. Select **Configure service backups**, then **S3 Compliant** (not Azure), then **Next**.
3. Enter the **second-cluster S3 HTTPS endpoint**, **generated bucket name**, access key, secret key, and certificate Secret name `lab02-service-protection-cert`.
4. Select **Add**. Verify location `service-protection-location` becomes **Connected**.
5. Select **Define schedule**. In this lab set **Daily**, **12:00 AM–4:00 AM**, timezone **America/Los_Angeles**, **30 days** retention, and **Initiate Service backup now = On**.
6. Select **Create policy**. Verify the service backup transitions through snapshot processing to **Completed**, backup count **1**, connected location, scheduled policy visible.

**Validated observed result**: First Service Protection backup completed November 13, 2026 at 11:26 AM PST, size <0.01 GiB; this verifies a successful service backup, not a destructive disaster-recovery test. S3 bucket was on the separate `itz-2xvmb0` cluster. UI configuration is a documented supported/manual stage; Ansible should validate prerequisites and report results around it, not claim to configure the UI automatically.

## v0.6 — Spoke bootstrap (UI to generate, Ansible/oc to deploy)

**Preflight**: Confirm spoke Fusion 2.14.1, backup agent not already installed, available `ocs-storagecluster-ceph-rbd` StorageClass, and hub Kafka bootstrap/broker/bridge routes. Original observed state on spoke: `ibm-backup-restore` namespace absent and only `odfmanager` FusionServiceInstance present.

**Manual IBM Fusion hub UI**:

1. Open **Backup & restore → Topology → Connect cluster → Automate deployment** on the HUB.
2. Enter the spoke's StorageClass `ocs-storagecluster-ceph-rbd`. Fusion calls for at least **34 GiB** of ReadWriteOnce snapshot-capable storage.
3. Select **Generate → Deploy using YAML → Download YAML**.
4. Save as `BackupAndRestoreAgentDeployment.yaml` and transfer to Ubuntu by `scp`. **The token expires after one hour**. Restrict local permissions to `chmod 600` and **NEVER commit the YAML** to GitHub.
5. Verify `oc --kubeconfig=$HOME/.kube/lab01.conf whoami --show-server` identifies the spoke API. Validate with `oc --kubeconfig=$HOME/.kube/lab01.conf apply --dry-run=server -f BackupAndRestoreAgentDeployment.yaml`, then run the actual `oc ... apply -f ...` or an Ansible command task with the same explicit spoke kubeconfig.
6. The generated configuration creates bootstrap Secret, Connection custom resource, and `ibm-backup-restore-agent-service-instance` in the spoke Fusion namespace. Monitor status until `Completed`, deployments available.
7. On HUB **Backup & restore → Topology**, verify spoke is listed as **Connected** and **Healthy**, matching Fusion version 2.14.1.

**Validated observed result**: Spoke agent installation Completed with 8/8 deployments available and hub UI displayed two clusters, hub `itz-t63twk` Healthy and spoke `itz-2xvmb0` Connected/Healthy.

## v0.7 — Cross-cluster FileBrowser recovery

**Prerequisites**: Source hub FileBrowser S3 backup `filebrowser-lab02-v03-backup` `Completed`, S3 BackupStorageLocation `hubspoke-bucket` `Connected`, spoke able to reach the hub S3 endpoint, spoke storage class present, and no conflicting target namespace.

**Ansible**: The one-command `scripts/run-lab02.sh` executes `installer/07-crosscluster-filebrowser-restore.yml` in this consolidated repository. It recognizes the registered spoke's actual `Cluster` resource name (`apps.itz-2xvmb0.infra01-lb.wdc04.techzone.ibm.com`) and creates a managed hub Restore CR only if absent, using `targetCluster` and `overwrite: false`. It waits for completion, checks the restored FileBrowser deployment and both PVCs on the spoke, then verifies the original 8 MiB file's SHA-256 on both clusters. A repeated run is designed to report `changed=0 failed=0`.

**Validated observed result before packaging**: Hub Restore `filebrowser-lab02-v07-restore` **Completed**, spoke FileBrowser pod **1/1 Running**, `files` (10 GiB) and `filebrowser-config` (1 GiB) PVCs **Bound**, SHA-256 identical on both clusters: `caf85e4ede776f0a8ab82bae96ae0ec126f8ce8f3fb8ff6c0dcc8c585a2d608b`.
