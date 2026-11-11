# Field validation summary

| Release | Reservation | Date | Outcome |
|---|---|---|---|
| **v2.2** | Fresh nine-node TechZone OCP 4.21.24 cluster | November 11, 2026 | **PASS — all seven stages** |
| v1.4.2 component scripts | Earlier TechZone OCP 4.21.24 cluster | November 2026 | PASS after incremental integration |
| **v2.3** | Not yet deployed to a fresh reservation | — | **Offline tests only** |

The **v2.2** single-command run installed IBM Fusion 2.14.1, configured three local Ceph OSDs, created a separate three-node Scale client pool, enabled the Scale operator, connected to an existing external Scale server, mounted `fs1`, and created `fusionfs1`.

Both storage backends passed a **16 MiB write, writer-pod removal, remount into a fresh reader pod and SHA-256 checksum**. Temporary test namespaces were deleted. A transient Scale operator readiness assertion was handled automatically by the runner's retry logic; no manual deployment intervention was needed.

**Timing:** the installer log filename places startup at **20:31:58 UTC**; Scale I/O validation passed at **21:11:33 UTC**; final verification followed. The full deployment took **approximately 40 minutes**, excluding earlier preparation and test planning. Exact process-exit time was not timestamped by v2.2.

Details: [observed field-test record](docs/06-LIVE-VALIDATION-2026-11-11.md).

The earlier v1.4.2 validation and the v2.2 fresh-cluster validation are **not** evidence that the v2.3 changes have been tested in a new reservation. v2.3 preserves the tested installation stages but improves readiness handling and console output.
