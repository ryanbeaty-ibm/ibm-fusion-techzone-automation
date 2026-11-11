"""Offline wiring and read-only-policy tests for the v2.2 Ansible health gate."""
import importlib.util
import pathlib
import subprocess
from unittest import mock
import yaml

root = pathlib.Path(__file__).resolve().parents[1]
playbook = root / 'installer' / 'cluster-health.yml'
plays = yaml.safe_load(playbook.read_text())
assert len(plays) == 1
assert plays[0]['gather_facts'] is False
for task in plays[0]['tasks']:
    assert set(task) & {'ansible.builtin.command', 'ansible.builtin.assert', 'ansible.builtin.debug'}
    assert 'ansible.builtin.shell' not in task
    if 'ansible.builtin.command' in task:
        assert task['changed_when'] is False
        argv = task['ansible.builtin.command']['argv']
        assert 'oc' == argv[0] and 'get' in argv
print('PASS: Ansible health play contains read-only commands and assertions')

spec=importlib.util.spec_from_file_location('lab01_v22',root/'installer'/'techzone_lab01.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
p={'cluster':'itz-test123','kubeconfig':'/tmp/example-test.conf','api':'https://api.itz-test123.infra01-lb.wdc07.techzone.ibm.com:6443'}
with mock.patch.object(mod.shutil,'which',return_value='/usr/bin/ansible-playbook'), \
     mock.patch.object(mod.subprocess,'run',return_value=subprocess.CompletedProcess([],0)) as run:
    mod.run_cluster_health_gate(p,root/'work/itz-test123')
    args,kw=run.call_args
    assert 'ansible-playbook' == args[0][0]
    assert str(playbook) in args[0]
    assert kw['env']['KUBECONFIG']==p['kubeconfig']
print('PASS: both action paths invoke pinned Ansible health checks')
with mock.patch.object(mod.shutil,'which',return_value='/usr/bin/ansible-playbook'), \
     mock.patch.object(mod.subprocess,'run',return_value=subprocess.CompletedProcess([],2)):
    try: mod.run_cluster_health_gate(p,root/'work/itz-test123')
    except SystemExit as e: assert 'preflight FAILED' in str(e)
    else: raise AssertionError('Missing fail-closed preflight behavior')
print('PASS: unhealthy preflight stops workflow')

src=(root/'installer'/'techzone_lab01.py').read_text()
assert src.index('run_cluster_health_gate(params, folder)') < src.index('if args.action == \'plan\':')
assert src.index('run_cluster_health_gate(params, folder)') < src.index('execute(params, folder, args.start_stage, vault=vault)')
print('PASS: plan and deploy call the health gate before any installation')
