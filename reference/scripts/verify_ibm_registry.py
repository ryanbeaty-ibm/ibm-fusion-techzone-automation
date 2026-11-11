#!/usr/bin/env python3
"""Read-only IBM entitled registry probe using only the target kubeconfig.

Only reads OpenShift's pull-secret and remote OCI image metadata. Creates a
mode-0600 local temporary auth file and deletes it. Never outputs credentials.
No external Python dependencies or Docker/Podman/Skopeo required.
"""
import argparse
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

IMAGE = re.compile(r'^cp\.icr\.io/cp/[A-Za-z0-9._/-]+@sha256:[a-f0-9]{64}$')


def fail(code, reason):
    print(json.dumps({'verified': False, 'reason': reason}, sort_keys=True))
    return code


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--kubeconfig', required=True)
    p.add_argument('--expected-api', required=True)
    p.add_argument('--protected-api', default='')
    p.add_argument('--image', required=True)
    args = p.parse_args()

    # Avoid testing a public image or using an accidental old-lab target.
    if not IMAGE.fullmatch(args.image):
        return fail(2, 'INVALID_PROTECTED_IMAGE_REFERENCE')
    if (not args.expected_api.startswith('https://') or
            args.expected_api == args.protected_api or
            not Path(args.kubeconfig).is_file()):
        return fail(2, 'INVALID_CLUSTER_PIN')

    def oc(*params):
        return subprocess.run(
            ['oc', '--kubeconfig=' + args.kubeconfig, *params],
            capture_output=True, text=True, timeout=40, check=False)

    try:
        api = oc('whoami', '--show-server')
        if api.returncode != 0 or api.stdout.strip() != args.expected_api:
            return fail(3, 'TARGET_API_MISMATCH_OR_UNREACHABLE')
        raw = oc('get', 'secret', 'pull-secret', '-n', 'openshift-config', '-o', 'json')
        if raw.returncode != 0:
            return fail(4, 'TARGET_PULL_SECRET_UNREADABLE')
        value = json.loads(raw.stdout)['data']['.dockerconfigjson']
        docker = json.loads(base64.b64decode(value, validate=True))
        auths = docker.get('auths', {})
        # Host names may be represented with a leading https://.
        auth = next((v for h, v in auths.items()
                     if h.rstrip('/').removeprefix('https://') == 'cp.icr.io'), None)
        if not isinstance(auth, dict) or not (auth.get('auth') or
                                              (auth.get('username') and auth.get('password')) or
                                              auth.get('identitytoken')):
            return fail(5, 'IBM_ENTITLEMENT_CREDENTIAL_MISSING')

        # No CLI argument ever contains an entitlement key; the auth-file path
        # is a private, temporary path, not an upload or cluster resource.
        with tempfile.TemporaryDirectory(prefix='ibm-fusion-registry-') as directory:
            config = Path(directory) / 'config.json'
            fd = os.open(str(config), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'w') as handle:
                json.dump(docker, handle)
            probe = subprocess.run(
                ['oc', 'image', 'info', '--registry-config=' + str(config), args.image],
                capture_output=True, text=True, timeout=90, check=False)
        if probe.returncode != 0:
            msg = (probe.stderr + ' ' + probe.stdout).lower()
            if any(x in msg for x in ['unauthorized', 'denied', 'forbidden', '401', '403']):
                return fail(6, 'REGISTRY_AUTH_OR_ENTITLEMENT_DENIED')
            if any(x in msg for x in ['manifest unknown', 'not found', '404']):
                return fail(7, 'REGISTRY_IMAGE_NOT_FOUND')
            return fail(8, 'REGISTRY_REQUEST_FAILED')
        print(json.dumps({'verified': True, 'reason': 'ENTITLED_IMAGE_MANIFEST_READABLE',
                          'image': args.image, 'api': args.expected_api}, sort_keys=True))
        return 0
    except subprocess.TimeoutExpired:
        return fail(9, 'REQUEST_TIMED_OUT')
    except (KeyError, ValueError, TypeError, UnicodeError, json.JSONDecodeError):
        return fail(10, 'MALFORMED_PULL_SECRET')
    except OSError:
        return fail(11, 'LOCAL_EXECUTION_ERROR')


if __name__ == '__main__':
    sys.exit(main())
