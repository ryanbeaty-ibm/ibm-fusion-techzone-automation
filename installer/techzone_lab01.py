#!/usr/bin/env python3
"""Prepare and run one isolated, explicitly approved IBM Fusion TechZone Lab 01.

Compiles the user-proven v1.4.2 scripts for the current cluster, without changing
legacy source files or guessing any remote cluster ID. Python stdlib + PyYAML.
"""
import argparse
import getpass
import secrets
import stat
import tempfile
import datetime
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
import textwrap

HERE = pathlib.Path(__file__).resolve().parent.parent
REFERENCE = HERE / 'reference'
RELEASE = '2.3.0'
STAGES = (
    'fusion-ceph',
    'ceph-io-test',
    'scale-nodeprep',
    'scale-operator',
    'scale-client',
    'scale-external',
    'final-verification',
)
BASE_PREFIX = 'itz-s6fyum'
BASE_API = 'https://api.itz-s6fyum.infra01-lb.wdc04.techzone.ibm.com:6443'
BASE_KCFG = '/home/automation/.kube/lab01.conf'
BASE_SCALE_NAME = 'lab01-external-scale'
BASE_SCALE_HOST = '10.10.10.202'


def stop(message):
    raise SystemExit('STOP: ' + message)


def call_oc(kcfg, *parts):
    try:
        return subprocess.check_output(['oc', f'--kubeconfig={kcfg}', *parts], text=True, timeout=45).strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as exc:
        stop(f'Cannot query OpenShift ({" ".join(parts)}): {exc}')


def validate_cluster(args):
    if shutil.which('oc') is None:
        stop('OpenShift oc command not installed or not in PATH.')
    kcfg = pathlib.Path(args.kubeconfig).expanduser().resolve()
    if not kcfg.is_file() or not kcfg.stat().st_size:
        stop(f'Kubeconfig missing: {kcfg}')
    if kcfg == pathlib.Path.home() / '.kube/config':
        stop('Use a named lab kubeconfig rather than the implicit ~/.kube/config.')
    if not re.fullmatch(r'itz-[a-z0-9-]{5,40}', args.cluster):
        stop('Expected an explicit TechZone cluster prefix such as itz-s6fyum.')
    if not re.fullmatch(r'/dev/[a-zA-Z0-9]+', args.ceph_disk) or args.ceph_disk in ('/dev/sda', '/dev/vda', '/dev/nvme0n1'):
        stop('Invalid or unsafe Ceph disk argument.')
    if not re.fullmatch(r'[A-Za-z0-9.\-]+', args.scale_host) or len(args.scale_host) > 253:
        stop('Scale server must be an IP or DNS hostname, not a URL.')
    if args.device_min_bytes < 400_000_000_000:
        stop('Minimum Ceph disk size cannot be below the tested 400GB requirement.')
    if not (re.fullmatch(r'[1-9][0-9]*Gi', args.ceph_pvc_request)):
        stop('Ceph PVC request must be a quantity such as 400Gi.')
    api = call_oc(kcfg, 'whoami', '--show-server')
    if not re.fullmatch(r'https://api\.[a-z0-9.-]+\.techzone\.ibm\.com:6443', api):
        stop(f'API is not an expected IBM TechZone address: {api}')
    if f'api.{args.cluster}.' not in api:
        stop(f'Cluster prefix {args.cluster} does not match API {api}')
    who = call_oc(kcfg, 'whoami')
    if who != 'system:admin':
        stop(f'Expected lab system:admin, got {who}')
    try:
        data = json.loads(call_oc(kcfg, 'get', 'nodes', '-o', 'json'))
        version = json.loads(call_oc(kcfg, 'get', 'clusterversion', 'version', '-o', 'json'))['status']['desired']['version']
    except (KeyError, ValueError) as exc:
        stop(f'Unexpected OpenShift inventory JSON: {exc}')
    if not version.startswith('4.21.'):
        stop(f'Tested with OpenShift 4.21.x only, actual version is {version}.')
    expect = sorted(f'{args.cluster}-{role}-{num}' for role in ('master', 'infra', 'worker') for num in (1, 2, 3))
    actual = sorted(x['metadata']['name'] for x in data['items'])
    if actual != expect:
        stop(f'Expected exactly nine nodes for {args.cluster}. Actual: {actual}')
    for n in data['items']:
        name = n['metadata']['name']
        conditions = n.get('status', {}).get('conditions', [])
        if not any(x.get('type') == 'Ready' and x.get('status') == 'True' for x in conditions):
            stop(f'Node is not Ready: {name}')
        labels = n['metadata'].get('labels', {})
        if '-infra-' in name or '-worker-' in name:
            if 'node-role.kubernetes.io/worker' not in labels:
                stop(f'Expected a Kubernetes worker-role label on {name}')
    return {'api': api, 'whoami': who, 'version': version, 'kubeconfig': str(kcfg),
            'cluster': args.cluster, 'scale_host': args.scale_host,
            'ceph_disk': args.ceph_disk, 'device_min_bytes': args.device_min_bytes,
            'ceph_pvc_request': args.ceph_pvc_request, 'version_bundle': RELEASE}


def safe_replace(text, params, filename):
    new_scale_name = f"{params['cluster']}-external-scale"
    replacements = {
        BASE_API: params['api'],
        BASE_KCFG: params['kubeconfig'],
        BASE_PREFIX: params['cluster'],
        BASE_SCALE_NAME: new_scale_name,
        BASE_SCALE_HOST: params['scale_host'],
    }
    # Single-pass substitution: a new generated name must never be rewritten
    # again if it happens to contain a substring of a legacy name.
    pattern = re.compile('|'.join(re.escape(k) for k in sorted(replacements, key=len, reverse=True)))
    text = pattern.sub(lambda match: replacements[match.group(0)], text)
    if params['cluster'] != BASE_PREFIX and BASE_PREFIX in text:
        stop(f'Compiler left a stale node identity in {filename}')
    if params['api'] != BASE_API and BASE_API in text:
        stop(f'Compiler left a stale API endpoint in {filename}')
    if params['kubeconfig'] != BASE_KCFG and BASE_KCFG in text:
        stop(f'Compiler left a stale kubeconfig path in {filename}')
    if BASE_SCALE_NAME != new_scale_name and BASE_SCALE_NAME in text:
        stop(f'Compiler left a stale Scale filesystem identity in {filename}')
    return text


def yaml_write(path, value):
    import yaml
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('# Generated from the explicitly checked TechZone cluster.\n'
                    + yaml.safe_dump(value, sort_keys=False))
    path.chmod(0o600)


def reference_fingerprint():
    h = hashlib.sha256()
    for f in sorted(REFERENCE.rglob('*')):
        if f.is_file():
            h.update(str(f.relative_to(REFERENCE)).encode())
            h.update(f.read_bytes())
    return h.hexdigest()


def workspace(params):
    folder = HERE / 'work' / params['cluster']
    stamp = {'params': params, 'reference_sha256': reference_fingerprint()}
    manifest = folder / 'generation.json'
    if manifest.exists():
        if json.loads(manifest.read_text()) != stamp:
            stop(f'Existing workspace {folder} was created for different settings/source. '
                 'Preserve it and use a fresh directory after reviewing differences.')
        print(f'REUSING pinned workspace {folder}', flush=True)
        return folder
    if folder.exists():
        stop(f'Workspace exists without generation manifest: {folder}. Refusing to overwrite it.')
    folder.mkdir(parents=True, mode=0o700)
    for part in ('playbooks', 'templates', 'scripts', 'config'):
        shutil.copytree(REFERENCE / part, folder / part)
    # Compile only the proven Lab 01 playbooks and scripts. Historical source
    # remains untouched under reference/ and must never be used as a live target.
    for file in [*(folder / 'playbooks').glob('lab01-*.yml'),
                 *(folder / 'scripts').glob('lab01-*.sh'),
                 *(folder / 'templates').glob('*lab01*.j2')]:
        file.write_text(safe_replace(file.read_text(), params, str(file)))
    import yaml
    prefix = params['cluster']
    infra = [f'{prefix}-infra-{i}' for i in (1, 2, 3)]
    workers = [f'{prefix}-worker-{i}' for i in (1, 2, 3)]
    target = {
        'kubeconfig_path': params['kubeconfig'],
        'expected_api_server': params['api'],
        'protected_api_server': 'https://never-use.invalid:6443',
        'expected_ocp_minor': '4.21',
        'expected_fusion_csv': 'isf-operator.v2.14.1',
    }
    disks = {
        'odf_storage_nodes': infra,
        'odf_candidate_device': params['ceph_disk'],
        'odf_min_disk_bytes': params['device_min_bytes'],
        'odf_require_nonrotational': True,
        'odf_local_volume_name': 'fusion-ceph-local',
        'odf_local_storage_class': 'fusion-ceph-local',
        'odf_pvc_request': params['ceph_pvc_request'],
    }
    client = {
        'kubeconfig': params['kubeconfig'], 'scale_namespace': 'ibm-spectrum-scale',
        'scale_name': f'{prefix}-external-scale', 'scale_license': 'data-access',
        'scale_nodes': workers, 'scale_node_label_key': 'demo.ibm.com/scale-client',
        'scale_node_label_value': 'true', 'scale_apply_enabled': False,
    }
    external = {
        'kubeconfig': params['kubeconfig'], 'scale_namespace': 'ibm-spectrum-scale',
        'scale_name': f'{prefix}-external-scale', 'scale_management_host': params['scale_host'],
        'scale_management_port': 443,
        'scale_gui_secret_name': f'{prefix}-external-scale-gui', 'scale_filesystem': 'fs1',
        'scale_storageclass': 'fusionfs1', 'scale_nodes': workers,
        'scale_insecure_skip_verify': True, 'scale_apply_enabled': False,
    }
    for name, data in [('lab01.yml', target), ('odf-lab01.yml', disks),
                       ('lab01-scale-client.yml', client), ('lab01-scale-external.yml', external)]:
        yaml_write(folder / 'config/local' / name, data)
    (folder / 'logs').mkdir(mode=0o700)
    manifest.write_text(json.dumps(stamp, indent=2, sort_keys=True) + '\n')
    manifest.chmod(0o600)
    print(f'CREATED pinned workspace {folder}', flush=True)
    return folder




def scale_vault_paths(cluster):
    """Credential files live in the operator's home, never in the project/worktree."""
    base = pathlib.Path.home() / '.config' / 'fusion-lab01'
    return base / 'credentials' / f'{cluster}.vault.yml', base / 'vault-keys' / f'{cluster}.key'


def private_dir(path):
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.is_symlink() or not path.is_dir():
        stop(f'Credential directory must be a real directory: {path}')
    if stat.S_IMODE(path.stat().st_mode) & 0o077:
        stop(f'Credential directory must not be accessible to group/others: {path} (chmod 700 it)')


def require_private_regular(path):
    if path.is_symlink() or not path.is_file() or not path.stat().st_size:
        stop(f'Missing, empty, or symlinked credential file: {path}')
    if stat.S_IMODE(path.stat().st_mode) & 0o077:
        stop(f'Credential file must be user-only: {path} (chmod 600 it)')


def vault_encrypt_string(vault_key, name, value):
    # Secret material goes through stdin only, never argv, environment, logs or disk in plaintext.
    result = subprocess.run(
        ['ansible-vault', 'encrypt_string', '--vault-password-file', str(vault_key), '--stdin-name', name],
        input=value, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=40, check=False,
    )
    if result.returncode or '!vault |' not in result.stdout or '$ANSIBLE_VAULT' not in result.stdout:
        stop('Ansible Vault encryption failed. Check that ansible-vault is installed and functional.')
    return result.stdout.strip() + '\n'


def configure_scale_vault(cluster, update=False):
    vault_file, key_file = scale_vault_paths(cluster)
    private_dir(vault_file.parent.parent)
    private_dir(vault_file.parent)
    private_dir(key_file.parent)
    if vault_file.exists() and not update:
        require_private_regular(vault_file)
        require_private_regular(key_file)
        print(f'Using saved, encrypted Scale GUI credentials for {cluster}; no login prompts.', flush=True)
        return vault_file, key_file
    if vault_file.exists():
        require_private_regular(vault_file)
        require_private_regular(key_file)
    if shutil.which('ansible-vault') is None:
        stop('ansible-vault is required to encrypt and reuse Scale GUI credentials.')
    if not sys.stdin.isatty():
        stop('Initial credential setup requires an interactive terminal (no --password on the command line).')
    print('=== IBM Storage Scale GUI credentials (stored using Ansible Vault) ===', flush=True)
    username = input('Scale GUI username [csi-storage-gui-user]: ').strip() or 'csi-storage-gui-user'
    password = getpass.getpass('Scale GUI password (hidden): ')
    if not username or not password or any(c in username + password for c in ('\n','\r','\0')):
        stop('A nonempty, single-line username/password is required.')
    if not key_file.exists():
        # Convenience mode: the random key is local-only and saved OUTSIDE the repo.
        fd = os.open(key_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd,'w') as out:
            out.write(secrets.token_urlsafe(48) + '\n')
    require_private_regular(key_file)
    encrypted = (
        '# Ansible Vault encrypted GUI credentials; DO NOT COMMIT.\n'
        + vault_encrypt_string(key_file, 'scale_remote_gui_username', username)
        + vault_encrypt_string(key_file, 'scale_remote_gui_password', password)
    )
    # Atomic replacement; never write a plaintext credential file.
    fd, temp_path = tempfile.mkstemp(prefix='.vault-', suffix='.tmp', dir=vault_file.parent)
    try:
        with os.fdopen(fd, 'w') as out:
            out.write(encrypted)
        os.chmod(temp_path, 0o600)
        os.replace(temp_path, vault_file)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    print(f'Encrypted GUI credentials saved outside the repository: {vault_file}', flush=True)
    print('A separate user-only local Vault key enables unattended reuse on this Ubuntu host.', flush=True)
    return vault_file, key_file


def run_cluster_health_gate(params, directory):
    """Execute read-only Ansible readiness checks before any installer writes."""
    if shutil.which('ansible-playbook') is None:
        stop('ansible-playbook is required for the automatic cluster health preflight.')
    playbook = HERE / 'installer' / 'cluster-health.yml'
    if not playbook.is_file():
        stop(f'Missing cluster health preflight: {playbook}')
    argv = ['ansible-playbook', '-i', 'localhost,', str(playbook),
            '-e', f"lab_preflight_kubeconfig={params['kubeconfig']}",
            '-e', f"lab_preflight_cluster={params['cluster']}",
            '-e', f"lab_preflight_api={params['api']}"]
    print('=== Automatic read-only OpenShift health preflight (Ansible) ===', flush=True)
    env = dict(os.environ, KUBECONFIG=params['kubeconfig'])
    result = subprocess.run(argv, cwd=HERE, env=env, check=False)
    if result.returncode:
        stop('Read-only OpenShift preflight FAILED; not installing anything. '
             'Review the failing ClusterOperator/MachineConfigPool and rerun after recovery.')
    print('PASS: OpenShift readiness gate. Disk eligibility is checked immediately before Ceph claims; '
          'Scale connectivity is verified during the external connection stage.', flush=True)


def steps():
    def ans(playbook, *extras):
        config = 'config/local/lab01-scale-external.yml' if ('remote' in playbook or 'filesystem' in playbook) else 'config/local/lab01-scale-client.yml'
        return ['ansible-playbook', '-i', 'localhost,', playbook,
                '-e', '@' + config, '-e', 'scale_apply_enabled=true', *extras]
    return {
        'fusion-ceph': [
            ['bash', 'scripts/deploy-fusion-odf-lab.sh', 'config/local/lab01.yml',
             'config/local/odf-lab01.yml', '--claim-disks']],
        'ceph-io-test': [
            ['bash', 'scripts/test-fusion-ceph-io-lab.sh', 'config/local/lab01.yml']],
        'scale-nodeprep': [
            ans('playbooks/lab01-scale-nodeprep-render.yml'),
            ans('playbooks/lab01-scale-nodeprep-activate.yml'),
            ans('playbooks/lab01-scale-nodeprep-kernel.yml')],
        'scale-operator': [ans('playbooks/lab01-scale-activate-operator.yml')],
        'scale-client': [
            ans('playbooks/lab01-scale-render-client.yml'),
            ans('playbooks/lab01-scale-deploy-client.yml')],
        'scale-external': [['bash', 'scripts/lab01-scale-external.sh', 'deploy']],
        'final-verification': [
            ['bash', 'scripts/verify-fusion-odf-lab.sh', 'config/local/lab01.yml',
             'config/local/odf-lab01.yml']],
    }


def execute(params, directory, start_stage, vault=None):
    if not shutil.which('ansible-playbook') or not shutil.which('jq'):
        stop('Ansible and jq are required on the Ubuntu automation server.')
    log_path = directory / 'logs' / f"install-{datetime.datetime.now(datetime.timezone.utc):%Y%m%dT%H%M%SZ}.log"
    print(f'DEPLOYMENT LOG: {log_path}', flush=True)
    started = time.monotonic()
    env = dict(os.environ, KUBECONFIG=params['kubeconfig'])
    if vault:
        env['FUSION_SCALE_VAULT_VARS_FILE'] = str(vault[0])
        env['FUSION_SCALE_VAULT_PASSWORD_FILE'] = str(vault[1])
    def cmd(command, stage, attempt=1):
        # No command-line passwords. Credentials in the disposable lab playbook
        # are handled by Ansible no_log when creating the GUI Secret.
        message = f'=== {stage} [{attempt}]: {" ".join(command)} ==='
        print(message, flush=True)
        with log_path.open('a') as out:
            out.write(message + '\n')
            try:
                proc = subprocess.Popen(command, cwd=directory, env=env, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, text=True, errors='replace', bufsize=1)
            except OSError as exc:
                stop(f'Cannot start {stage}: {exc}')
            for line in proc.stdout:
                print(line, end='', flush=True)
                out.write(line)
            return proc.wait()
    begin = STAGES.index(start_stage)
    for stage in STAGES[begin:]:
        stage_started = time.monotonic()
        for part in steps()[stage]:
            attempts = 3 if stage == 'scale-operator' else 1
            for n in range(1, attempts + 1):
                rc = cmd(part, stage, attempt=n)
                if rc == 0:
                    break
                if n < attempts:
                    print(f'Scale operator activation exited with rc={rc}; retrying this same stage in 30s ({n}/{attempts}).', flush=True)
                    time.sleep(30)
            if rc:
                stop(f'Stage {stage} failed (rc={rc}). See {log_path}. '
                     f'Resume using --from {stage} after correcting the cause.')
        stage_elapsed = time.monotonic() - stage_started
        summary = f'PASS: {stage} (elapsed {int(stage_elapsed // 60)}m {int(stage_elapsed % 60):02d}s)'
        print(summary, flush=True)
        with log_path.open('a') as out:
            out.write(summary + '\n')
    total = time.monotonic() - started
    summary = 'PASS: ALL LAB 01 INSTALLATION AND STORAGE TEST STAGES.'
    print(summary, flush=True)
    print(f'DEPLOYMENT ELAPSED: {int(total // 60)}m {int(total % 60):02d}s (excludes preflight and credential entry)', flush=True)
    print('The remote IBM Storage Scale server was never installed or rebuilt by this workflow.', flush=True)
    with log_path.open('a') as out:
        out.write(summary + '\n')
        out.write(f'DEPLOYMENT ELAPSED: {int(total // 60)}m {int(total % 60):02d}s\n')


def parse(argv):
    ap = argparse.ArgumentParser(description='IBM Fusion Lab 01: a guarded single-command installer for new TechZone clusters.')
    ap.add_argument('action', choices=('plan', 'deploy'), help='plan is read-only; deploy changes only the specified lab')
    ap.add_argument('--cluster', required=True, help='Exact TechZone node prefix, e.g. itz-s6fyum')
    ap.add_argument('--kubeconfig', required=True, help='Explicit path to NEW lab kubeconfig')
    ap.add_argument('--scale-host', required=True, help='IP or DNS name of EXISTING external Scale server')
    ap.add_argument('--ceph-disk', required=True, help='Reviewed EMPTY disk path on all three infra nodes, e.g. /dev/vde')
    ap.add_argument('--device-min-bytes', type=int, default=400_000_000_000)
    ap.add_argument('--ceph-pvc-request', default='400Gi')
    ap.add_argument('--claim-disks', action='store_true', help='Authorize Ceph to consume the selected disks')
    ap.add_argument('--allow-worker-reboots', action='store_true', help='Authorize Scale MachineConfig worker reboots')
    ap.add_argument('--update-scale-credentials', action='store_true',
                    help='Re-prompt and replace locally encrypted Scale GUI credentials for this cluster')
    ap.add_argument('--from', dest='start_stage', default=STAGES[0], choices=STAGES,
                    help='Resume from a stage after a prior run; default is the whole installer')
    args = ap.parse_args(argv)
    if args.action == 'deploy' and not (args.claim_disks and args.allow_worker_reboots):
        stop('Deploy requires BOTH --claim-disks and --allow-worker-reboots.')
    if args.action == 'plan' and args.update_scale_credentials:
        stop('--update-scale-credentials is only supported with deploy.')
    return args


def main():
    args = parse(sys.argv[1:])
    params = validate_cluster(args)
    folder = workspace(params)
    run_cluster_health_gate(params, folder)
    print(f"TARGET: {params['cluster']} @ {params['api']} | OCP {params['version']} | user {params['whoami']}")
    print('NODES: 3 masters + 3 Ceph infra + 3 Scale application workers.')
    print(f"Ceph disk: {params['ceph_disk']} (explicit claim) | Pre-deployed remote Scale: {params['scale_host']}:443 / fs1")
    print('Scale backend = local mounted Filesystem CR name; remote Scale cluster ID discovered live.')
    if args.action == 'plan':
        print('PLAN ONLY. No cluster modifications were requested. Stage order:')
        for stage in STAGES:print('  -', stage)
        print(f'Rendered workspace: {folder}')
        return
    vault = None
    if STAGES.index(args.start_stage) <= STAGES.index('scale-external'):
        vault = configure_scale_vault(args.cluster, update=args.update_scale_credentials)
    elif args.update_scale_credentials:
        stop('Cannot update Scale credentials when resuming after the scale-external stage.')
    execute(params, folder, args.start_stage, vault=vault)


if __name__ == '__main__':
    main()
