# Maintainer guide — publish a Lab 1 installer ZIP

The repository's source code and its downloadable installer package serve different purposes. Publish each packaged `IBM-Fusion-Lab01-OneCommand-vX.Y.zip` as a **GitHub Release asset**, so new users can find a predictable download from the README.

## Before uploading

1. Locate the intended installer ZIP (for example, `IBM-Fusion-Lab01-OneCommand-v2.3.zip`) on your local machine.
2. Inspect its contents: verify it includes the expected installer files, and does **not** contain kubeconfig files, credentials, API tokens, SSH keys, `.env` secrets, or data taken from your active TechZone reservation.
3. Check the package validation record. The **v2.3 release asset** completed fresh-cluster OCP 4.21.24 installation and persistent-storage validation on **November 12, 2026**, **after a password correction and stage-level recovery**; see [the v2.3 record](07-LIVE-VALIDATION-2026-11-12.md). The first attempt failed at external Scale authentication, so do not describe v2.3 as a one-shot deployment success. The earlier v2.2 validation record is retained.
4. Optionally calculate a checksum in Windows PowerShell with the one-line command below, substituting the real ZIP filename and local path:

```powershell
Get-FileHash -Algorithm SHA256 'C:\Users\YOUR_USERNAME\Downloads\IBM-Fusion-Lab01-OneCommand-v2.3.zip'
```

## Publish in the GitHub website

1. Open the repository's [Releases page](https://github.com/ryanbeaty-ibm/ibm-fusion-techzone-automation/releases).
2. Choose **Draft a new release** (or **Create a new release**).
3. Choose a **new** tag matching the software version. **v2.3 was already published**, so do not overwrite or silently replace its release asset. If you change installer code, create a new version/tag (for example, the next version number chosen by the maintainer).
4. Enter a release title matching the **new** installer version.
5. In the description, list package contents, intended OCP/TechZone version, **exact validation status**, and known limitations. Keep a changed-but-not-yet-validated release labeled **pre-release**. v2.3 had a successful recovery but requires an installer improvement for early credential validation.
6. Upload the installer ZIP in the release **Assets** section, then publish the release.
7. Open the published release and check that the ZIP appears under **Assets** and downloads correctly.

GitHub generates source-code ZIPs automatically for release tags. Those are **not** the uploaded installer ZIP. Tell readers to select the installer ZIP under **Assets**.

This is a **website action**, separate from GitHub Desktop. Continue using GitHub Desktop to review, commit, and push repository documentation and source changes.
