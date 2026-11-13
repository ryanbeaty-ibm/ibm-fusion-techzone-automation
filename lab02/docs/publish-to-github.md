# Publish the Lab 02 package to an existing Git repository

The deliverable ZIP contains a **top-level `lab02/` directory**. Extract it into the **root of the existing Git repository**. Do not replace Lab 01 or other workspaces.

## Windows PowerShell — example

```powershell
# Download Fusion-Level4-Lab02-GitHub-Ready.zip to your normal Fusion download folder.
$Zip = 'D:\Dropbox\Fusion\level4_lab02\Fusion-Level4-Lab02-GitHub-Ready.zip'

# Find cloned Git repositories (one-level deep) before choosing the destination.
Get-ChildItem -Directory 'D:\GitHub' | Where-Object {
    Test-Path (Join-Path $_.FullName '.git')
} | Select-Object Name, FullName

# Validated existing local Git repository.
$Repo = 'D:\GitHub\ibm-fusion-techzone-automation'

# Extract into repo root; ZIP contains lab02/ so this creates $Repo\lab02\...
Expand-Archive -LiteralPath $Zip -DestinationPath $Repo -Force

# Inspect before committing. No credentials/tokens should appear.
git -C $Repo status --short
git -C $Repo diff --check
git -C $Repo add lab02
git -C $Repo diff --cached --stat
# Review staged changes, then commit/push when ready.
# Preferred: open GitHub Desktop, review the changes, then commit and Push origin.
# CLI alternative (optional):
# git -C $Repo commit -m 'Add IBM Fusion Level 4 Lab 02 backup and restore automation'
# git -C $Repo push
```

This project uses the existing clone `D:\GitHub\ibm-fusion-techzone-automation`. If `git -C $Repo status` fails, fix the repository path; do not commit or initialize another repository accidentally. For the most reliable approach, use the separate **Apply-IBM-Fusion-Lab02-GitHub.ps1** updater bundled alongside the downloadable ZIP; it stages outside the repository and then copies only `lab02/`. If the ZIP has a top-level `lab02/`, **extract at the Git root**, not into an existing `lab02/` (which would produce `lab02/lab02/`).

## Security check before pushing

```powershell
# Explicitly check for generated spoke deployment credentials and private configs.
git -C $Repo ls-files --cached | Select-String 'BackupAndRestoreAgentDeployment|kubeconfig|environment.yml|\.pem|\.key'
```

Do not commit generated secrets or actual kubeconfigs. Also inspect the Git diff for accidental keys in screenshots or pasted YAML. This package intentionally excludes screenshots and the vendor PDF. Repository owner decides on license/publication policy.
