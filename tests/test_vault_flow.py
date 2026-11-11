import importlib.util, tempfile, os, pathlib, unittest.mock as mock, subprocess
p=str(pathlib.Path(__file__).resolve().parents[1] / 'installer/techzone_lab01.py')
spec=importlib.util.spec_from_file_location('lab01_v21',p); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
class StubResult:
    returncode=0
    stderr=''
    def __init__(self,name): self.stdout = f'{name}: !vault |\n          $ANSIBLE_VAULT;1.1;AES256\n          616263\n'
with tempfile.TemporaryDirectory() as home:
    seen=[]
    def run(cmd,**kwargs):
        assert cmd[0:2]==['ansible-vault','encrypt_string']
        assert cmd[2]=='--vault-password-file'
        assert cmd[4]=='--stdin-name'
        assert kwargs['input'] in ('csi-storage-gui-user','test-only-value')
        assert 'test-only-value' not in ' '.join(cmd)
        seen.append(kwargs['input'])
        return StubResult(cmd[-1])
    with mock.patch.object(pathlib.Path,'home',return_value=pathlib.Path(home)), mock.patch.object(mod.shutil,'which',return_value='/usr/bin/ansible-vault'), mock.patch.object(mod.sys.stdin,'isatty',return_value=True), mock.patch('builtins.input',return_value=''), mock.patch.object(mod.getpass,'getpass',return_value='test-only-value'), mock.patch.object(mod.subprocess,'run',side_effect=run):
        vault,key=mod.configure_scale_vault('itz-test123')
        assert len(seen)==2
        assert vault.read_text().count('!vault |')==2
        assert 'test-only-value' not in vault.read_text()
        assert vault.stat().st_mode & 0o777==0o600
        assert key.stat().st_mode & 0o777==0o600
        assert vault.parent.stat().st_mode & 0o777==0o700
        assert len(key.read_text().strip())>40
        old=vault.read_text()
        mod.configure_scale_vault('itz-test123')
        assert vault.read_text()==old and len(seen)==2
        mod.configure_scale_vault('itz-test123',update=True)
        assert len(seen)==4
print('PASS: initial prompt, encrypted vars, file permissions, reuse, reconfiguration, no plaintext in vault file or argv (mock ansible-vault)')
assert '--vault-password-file' in (pathlib.Path(__file__).resolve().parents[1] / 'reference/scripts/lab01-scale-external.sh').read_text()
assert '    scale_remote_gui_password:' not in (pathlib.Path(__file__).resolve().parents[1] / 'reference/playbooks/lab01-scale-connect-remote.yml').read_text()
print('PASS: runner wiring and no hardcoded GUI password')
