# Maintainer guide — publish a Lab 1 installer ZIP

The repository's source code and its downloadable installer package serve different purposes. Publish each packaged `IBM-Fusion-Lab01-OneCommand-vX.Y.zip` as a **GitHub Release asset**, so new users can find a predictable download from the README.

## Before uploading

1. Locate the intended installer ZIP (for example, `IBM-Fusion-Lab01-OneCommand-v2.3.zip`) on your local machine.
2. Inspect its contents: verify it includes the expected installer files, and does **not** contain kubeconfig files, credentials, API tokens, SSH keys, `.env` secrets, or data taken from your active TechZone reservation.
3. Check whether the package has actually passed end-to-end validation. The repository currently identifies **v2.3 as a cleanup candidate** and **v2.2 as the preceding fresh-cluster validated version**. Do not label v2.3 as validated unless you retest it.
4. Optionally calculate a checksum in Windows PowerShell with the one-line command below, substituting the real ZIP filename and local path:

```powershell
Get-FileHash -Algorithm SHA256 'C:\Users\YOUR_USERNAME\Downloads\IBM-Fusion-Lab01-OneCommand-v2.3.zip'
```

## Publish in the GitHub website

1. Open the repository's [Releases page](https://github.com/ryanbeaty-ibm/ibm-fusion-techzone-automation/releases).
2. Choose **Draft a new release** (or **Create a new release**).
3. Choose a tag matching the software version, such as `v2.3`. If it does not yet exist, create it from the appropriate commit on `main`. Do not re-use an existing tag for different package content.
4. Enter a title, such as `IBM Fusion Lab 1 Installer v2.3`.
5. In the description, list the package contents, intended OCP/TechZone version, validation status, and any known limitations. If v2.3 is still a cleanup candidate, **mark the release as a pre-release**.
6. Upload the installer ZIP in the release **Assets** section, then publish the release.
7. Open the published release and check that the ZIP appears under **Assets** and downloads correctly.

GitHub generates source-code ZIPs automatically for release tags. Those are **not** the uploaded installer ZIP. Tell readers to select the installer ZIP under **Assets**.

This is a **website action**, separate from GitHub Desktop. Continue using GitHub Desktop to review, commit, and push repository documentation and source changes.
