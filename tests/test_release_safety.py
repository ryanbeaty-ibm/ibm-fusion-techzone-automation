"""Static checks for v2.4 safety fixes; does not connect to OpenShift."""
from pathlib import Path
import yaml

root = Path(__file__).resolve().parents[1]
scale = yaml.safe_load((root / 'reference/playbooks/lab01-scale-activate-operator.yml').read_text())[0]
assertion = next(t for t in scale['tasks'] if t['name'] == 'Assert at least one Scale operator replica is ready')
wait = next(t for t in scale['tasks'] if t['name'].startswith('Wait for one ready Scale operator replica'))
assert scale['tasks'].index(wait) < scale['tasks'].index(assertion)
assert '--for=jsonpath={.status.readyReplicas}=1' in wait['ansible.builtin.command']['argv']
assert '--timeout=900s' in wait['ansible.builtin.command']['argv']
assert wait['changed_when'] is False

nodeprep = yaml.safe_load((root / 'reference/playbooks/lab01-scale-nodeprep-activate.yml').read_text())[0]
task = next(t for t in nodeprep['tasks'] if t['name'] == 'Ensure no unselected node already has the scale role')
assert "map(attribute='metadata.name')" in task['loop']
assert "node_info['items']" in task['loop']
assert task['when'] == 'item not in scale_nodes'
assert task['loop_control']['label'] == '{{ item }}'
assert 'node-role.kubernetes.io/scale' in task['ansible.builtin.assert']['that'][0]

ignore = (root / '.gitignore').read_text().splitlines()
for required in ('work/', '*.vault.yml', '*.vault.yaml', '*.vault-password', '*.key', '*.kubeconfig', 'config/local/'):
    assert required in ignore, f'Missing ignore pattern: {required}'
assert not any('\\n' in line for line in ignore)

code = (root / 'installer/techzone_lab01.py').read_text()
assert "RELEASE = '2.4.0'" in code
assert 'DEPLOYMENT ELAPSED:' in code
assert 'stage_elapsed = time.monotonic() - stage_started' in code

print('PASS: operator readiness waits for a ready replica')
print('PASS: node inventory guard avoids outputting full Node objects')
print('PASS: credential and workspace ignore patterns are line-separated')
print('PASS: deployment stage timing is recorded')
