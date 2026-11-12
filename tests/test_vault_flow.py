"""Offline Scale GUI confirmation, encryption, and reconfiguration regression checks."""
import importlib.util
import pathlib
import subprocess
import tempfile
from unittest import mock

root = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('lab01_v24', root / 'installer/techzone_lab01.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class StubResult:
    returncode = 0
    stderr = ''
    def __init__(self, name):
        self.stdout = f'{name}: !vault |\n          $ANSIBLE_VAULT;1.1;AES256\n          616263\n'

with tempfile.TemporaryDirectory() as home:
    seen = []
    def run(cmd, **kwargs):
        assert cmd[0:2] == ['ansible-vault', 'encrypt_string']
        assert cmd[2] == '--vault-password-file'
        assert cmd[4] == '--stdin-name'
        assert kwargs['input'] in ('csi-storage-gui-user', 'test-only-value')
        assert 'test-only-value' not in ' '.join(cmd)
        seen.append(kwargs['input'])
        return StubResult(cmd[-1])

    params = {'cluster': 'itz-test123', 'scale_host': '10.10.10.202', 'kubeconfig': '/tmp/test-kubeconfig'}
    with (mock.patch.object(pathlib.Path, 'home', return_value=pathlib.Path(home)),
          mock.patch.object(mod.shutil, 'which', return_value='/usr/bin/ansible-vault'),
          mock.patch.object(mod.sys.stdin, 'isatty', return_value=True),
          mock.patch('builtins.input', return_value=''),
          mock.patch.object(mod.getpass, 'getpass', side_effect=['bad-entry', 'test-only-value',
                                                                 'test-only-value', 'test-only-value',
                                                                 'test-only-value', 'test-only-value']),
          mock.patch.object(mod, 'verify_scale_gui_from_worker') as preflight,
          mock.patch.object(mod.subprocess, 'run', side_effect=run)):
        vault, key = mod.configure_scale_vault('itz-test123', params=params)
        assert preflight.call_count == 1
        assert preflight.call_args.args[1:] == ('csi-storage-gui-user', 'test-only-value')
        assert len(seen) == 2
        assert vault.read_text().count('!vault |') == 2
        assert 'test-only-value' not in vault.read_text()
        assert vault.stat().st_mode & 0o777 == 0o600
        assert key.stat().st_mode & 0o777 == 0o600
        assert vault.parent.stat().st_mode & 0o777 == 0o700
        assert len(key.read_text().strip()) > 40
        old = vault.read_text()
        mod.configure_scale_vault('itz-test123', params=params)
        assert vault.read_text() == old and len(seen) == 2
        assert preflight.call_count == 1   # encrypted credentials reused, not re-prompted
        mod.configure_scale_vault('itz-test123', update=True, params=params)
        assert len(seen) == 4 and preflight.call_count == 2

        # A live authentication rejection must not overwrite the existing Vault.
        with mock.patch.object(mod, 'verify_scale_gui_from_worker', side_effect=SystemExit('HTTP 403')):
            with mock.patch.object(mod.getpass, 'getpass', side_effect=['test-only-value', 'test-only-value']):
                try:
                    mod.configure_scale_vault('itz-test123', update=True, params=params)
                except SystemExit as exc:
                    assert '403' in str(exc)
                else:
                    raise AssertionError('Expected fail-closed authentication')
        assert vault.read_text() == old

# Three mismatches never get to encryption and never write any key material.
with mock.patch('builtins.input', return_value=''), mock.patch.object(mod.getpass, 'getpass',
    side_effect=['a','b','a','c','a','d']):
    try:
        mod.prompt_scale_gui_credentials()
    except SystemExit as exc:
        assert 'No credentials saved' in str(exc)
    else:
        raise AssertionError('Password mismatch did not stop after three attempts')

# The preflight uses only a short-lived node debug pod and transmits secret via stdin.
params = {'cluster':'itz-test123','scale_host':'10.10.10.202','kubeconfig':'/tmp/test-kubeconfig'}
with mock.patch.object(mod.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0,
               stdout='Starting pod/test-debug...\nFUSION_SCALE_HTTP=200\n', stderr='')) as run:
    mod.verify_scale_gui_from_worker(params, 'csi-storage-gui-user','test-only-value')
    cmd = run.call_args.args[0]
    kwargs = run.call_args.kwargs
    assert cmd[:4] == ['oc','--kubeconfig=/tmp/test-kubeconfig','debug','--tty=false']
    assert '--config' in cmd and cmd[-1] == '-'
    assert 'test-only-value' not in ' '.join(cmd)
    assert 'test-only-value' in kwargs['input']
    assert 'user = ' in kwargs['input']
    assert kwargs['stdout'] is subprocess.PIPE and kwargs['stderr'] is subprocess.PIPE
for status in ('401','403','000'):
    with mock.patch.object(mod.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0,
                  stdout='FUSION_SCALE_HTTP=' + status, stderr='')):
        try: mod.verify_scale_gui_from_worker(params, 'user','secret-value')
        except SystemExit as exc:
            assert status in str(exc)
            assert 'secret-value' not in str(exc)
        else: raise AssertionError(f'HTTP {status} did not stop before install')
print('PASS: confirmation, mismatch retry/abort, early validation, encrypted reuse/update, safe stdin')
assert '--vault-password-file' in (root / 'reference/scripts/lab01-scale-external.sh').read_text()
assert '    scale_remote_gui_password:' not in (root / 'reference/playbooks/lab01-scale-connect-remote.yml').read_text()
print('PASS: runner wiring and no hardcoded GUI password')
