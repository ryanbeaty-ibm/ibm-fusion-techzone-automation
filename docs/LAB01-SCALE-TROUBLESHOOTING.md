# IBM Fusion Lab 01 — External Storage Scale connection troubleshooting (v2.3)

This page documents the actual recovery tested on **November 12, 2026**: IBM Fusion, Ceph, and the local Scale client completed, but the **external Storage Scale** stage could not authenticate. After correcting the GUI password and resuming that stage, the full installation and persistence test passed.

> **Lab only.** Do not paste passwords, kubeconfig files, private keys, Vault files, or Kubernetes Secret content into GitHub. Do not restart the earlier successful installation stages just to repair a GUI password.

## Know which account is which

| Purpose | Username | Where to obtain its password |
| --- | --- | --- |
| OpenShift admin | `kubeadmin` | TechZone reservation → **Cluster Admin Password** |
| Existing Scale Linux VM / RDP | `itzuser` | TechZone reservation → **Bastion Password** (confirmed on the Lab 01 Scale VM) |
| Existing Scale GUI / REST API | `csi-storage-gui-user` | IBM Fusion lab guide, labeled **pages 30 and 76** |

The GUI account is **not** a Linux desktop account. The Bastion Password is **not** the Scale GUI password.

## Get into the existing Storage Scale Linux VM

1. Open the TechZone reservation → **Outputs** and locate **Bastion Password**.
2. Open **VM Remote Console**, find the existing `xxx-scale-2` / `xxx-scale-02` VM (the lab commonly shows `10.10.10.202`), and click **Console**.
3. Connect using **RDP** with username `itzuser` and the reservation's **Bastion Password**. If RDP is unavailable, the console offers **Use VNC instead**.
4. Open a Linux Terminal. If needed, run `sudo -i` for administrative access.
5. Inspect registered Scale GUI users without revealing their passwords:

   ```bash
   /usr/lpp/mmfs/gui/cli/lsuser
   ```

Check whether `csi-storage-gui-user` exists, is active, has the intended groups, and shows failed login attempts. **Do not assume a 403 is a lockout**; in the documented case the account was active with zero failed attempts.

## Test credentials from the right network location

The Ubuntu automation VM may **not** have direct access to the TechZone private Scale IP even when the OpenShift workers can access it. A timeout from Ubuntu alone does **not** prove the Scale server is unavailable. In the November 12 lab, Ubuntu received a connection timeout, while an OpenShift worker could reach the REST API.

In a terminal **on the Scale Linux VM** (not your Windows PowerShell or the Ubuntu control VM), use this read-only check, with your actual Scale host if different:

```bash
curl -ksS --connect-timeout 5 --max-time 15 -o /dev/null -w "HTTP %{http_code}\n" -u csi-storage-gui-user https://10.10.10.202/scalemgmt/v2/info
```

`curl` will ask for the Scale GUI account password **without echoing characters**. Do **not** add the password to the command line. The `-k` option ignores TLS certificate verification for this controlled TechZone lab; do not use it indiscriminately in production.

| Result | Interpretation |
| --- | --- |
| `HTTP 200` | This account can reach and authenticate to this REST endpoint. |
| `HTTP 401` | Server rejected the authentication credentials. |
| `HTTP 403` | The server denied the request; check the exact password, account state and permissions before trying again. |
| `HTTP 000` / timeout | The command did not obtain an HTTP response; investigate path/network/service availability. |

In the validated recovery, carefully re-entering the **lab-guide GUI password** changed `HTTP 403` to `HTTP 200`. Do not repeatedly guess passwords or reset a working Scale account.

**Security:** An OpenShift node `oc debug` session can record terminal input in debug pod logs. Avoid entering passwords interactively in a debug pod. Use the existing Scale Linux VM's terminal for this check instead.

## Inspect failed RemoteCluster without exposing Secret data

From Ubuntu:

```bash
oc --kubeconfig="$HOME/.kube/REPLACE_ME.conf" -n ibm-spectrum-scale describe remotecluster.scale.spectrum.ibm.com itz-REPLACE_ME-external-scale
```

Look for `Ready`, `Available`, `RegisterClientFailed`, `RestAPIUnavailable`, `401 Unauthorized`, `403 Forbidden`, or `503 Service Unavailable`. A transient `503` may reflect the local GUI starting up. A `401` or `403` from the **remote** REST endpoint requires an authentication/authorization check; the unavailability of a `Ready=True` condition during retry is not automatically a storage failure.

## Recover after verifying the Scale GUI password (v2.3)

Only use this procedure **if `fusion-ceph`, `ceph-io-test`, `scale-nodeprep`, `scale-operator`, and `scale-client` passed**, and `scale-external` failed. Confirm the original cluster, kubeconfig, Storage Scale host, and selected disposable disk before execution.

From the extracted Ubuntu installer directory:

```bash
bash install-lab01.sh deploy \
  --cluster itz-REPLACE_ME \
  --kubeconfig "$HOME/.kube/REPLACE_ME.conf" \
  --scale-host REPLACE_WITH_EXISTING_SCALE_IP \
  --ceph-disk /dev/vde \
  --claim-disks \
  --allow-worker-reboots \
  --update-scale-credentials \
  --from scale-external
```

**Important:** The current v2.3 CLI requires **both** `--claim-disks` and `--allow-worker-reboots` even with `--from scale-external`. These flags authorize destructive operations if the script were to run earlier stages. **Review the output and immediately stop if it unexpectedly starts at `fusion-ceph` or another previously completed stage.** The verified November 12 run resumed at `scale-external` only.

At the prompts, accept the intended Scale GUI username and type the **now-verified** password. The script re-prompts because `--update-scale-credentials` is present, refreshes the local Ansible Vault material, and applies the GUI Secret through the remote stage without printing its contents.

On successful recovery, the remote cluster reaches `Ready=True`, the external `fs1` filesystem mounts, the `fusionfs1` StorageClass is created/checked, the persistent-volume I/O test passes, and `final-verification` runs. The successful recovery on November 12 took **3m 03s** excluding preflight and password entry; this is **not** a guarantee of future performance.

### Optional read-only condition check

```bash
oc --kubeconfig="$HOME/.kube/REPLACE_ME.conf" -n ibm-spectrum-scale get remotecluster itz-REPLACE_ME-external-scale -o jsonpath='{range .status.conditions[*]}{.type}={.status} ({.reason}){"\n"}{end}'
```

Note: an intermediate Ansible summary on November 12 reported `Ready=True`, `Available=False`. The subsequent **filesystem mount and actual read/write I/O test passed**. Investigate persistent `Available=False` separately if it remains after reconciliation; do not equate one intermediate field with failed storage when post-mount tests passed.

## Improvements reserved for the next installer release (NOT in v2.3)

- Hidden **password + confirmation** prompts; reject mismatches before saving to Vault.
- Early REST API authentication and required-permission check from a network location **inside TechZone/OCP** (the Ubuntu VM may not directly reach the private Scale address), before any lengthy or destructive deployment.
- Fail fast and report `401`/`403` with clear troubleshooting guidance instead of waiting up to 30 minutes without useful diagnostics.
- Review whether later-stage `--from` recovery truly needs earlier-stage disk/reboot approval flags.

## v2.4 early authentication preflight

For new credentials or when running `deploy --update-scale-credentials`, v2.4 asks for the Scale GUI password twice and uses a temporary non-TTY debug pod on an OpenShift worker to make a read-only authenticated `GET /scalemgmt/v2/info` request. A 401 or 403 immediately stops deployment **before storage stages**; check the username, password and GUI account permissions. The Ubuntu automation VM cannot normally connect directly to the private Scale IP. If the node debug pod cannot be created, the preflight fails closed; check permissions and network routing. The early GET does not prove permission for all later remote-registration operations.

Previously saved credentials are reused without a new prompt unless you provide `--update-scale-credentials`. Resume commands still require `--claim-disks` and `--allow-worker-reboots` in v2.4.
