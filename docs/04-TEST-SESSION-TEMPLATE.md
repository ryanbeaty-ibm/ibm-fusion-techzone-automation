# 04 — Clean-room installer test worksheet

Copy this file to a new document for **each** TechZone deployment. Do **not** save private kubeconfig files, passwords, tokens, or unredacted logs in Git.

**Test date (UTC):** TBD  
**Installer version:** 2.0.0 (unless changed)  
**Git revision:** TBD  
**TechZone cluster prefix:** TBD  
**OpenShift version:** TBD  
**Remote Scale host:** [redact in public publication if needed]  
**Selected disposable Ceph disk:** TBD  
**Runner OS / Ansible / Python / `oc` versions:** TBD

## Preflight

- [ ] Lab reservation created and external Scale server identified
- [ ] Kubeconfig downloaded, transferred, restricted with `chmod 600`
- [ ] `oc whoami` and API endpoint verified
- [ ] Exactly nine expected nodes all Ready
- [ ] Confirmed selected local disks are unused and safe to claim
- [ ] v2.1 `plan` succeeded without cluster modifications

## Deployment outcomes

| Stage | Expected | Observed result | Duration / notes |
|---|---|---|---|
| `fusion-ceph` | PASS | Not run | |
| `ceph-io-test` | PASS | Not run | |
| `scale-nodeprep` | PASS | Not run | |
| `scale-operator` | PASS | Not run | |
| `scale-client` | PASS | Not run | |
| `scale-external` | PASS | Not run | |
| `final-verification` | PASS | Not run | |

## Persistent data proof

- Ceph: **PVC Bound:** ___  **Write:** ___  **Remount:** ___  **SHA-256:** ___
- Scale: **PVC Bound:** ___  **Write:** ___  **Remount:** ___  **SHA-256:** ___
- Both temporary namespaces cleaned up: ___
- Did operator or worker preparation require a manual intervention? ___

## Release decision

- [ ] Complete clean-room run without code changes
- [ ] Documentation commands verified as written
- [ ] Logs sanitized and useful failure details recorded
- [ ] Any necessary fixes committed, version bumped, and retested

**Result:** NOT YET TESTED / FAILED / PASSED (choose one after the run)
