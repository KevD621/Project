import docker
import json
import os
import tempfile

client = docker.from_env()

def build_sandbox_image():
    try:
        client.images.get('phish-sandbox')
    except docker.errors.ImageNotFound:
        print("Building sandbox image...")
        client.images.build(
            path='./docker_sandbox',
            tag='phish-sandbox',
            rm=True
        )

def run_sandbox(url):
    build_sandbox_image()
    # Run container with strict isolation
    container = client.containers.run(
        'phish-sandbox',
        command=f'node browse.js "{url}"',
        detach=True,
        remove=True,           # Auto-remove
        read_only=True,        # rootfs read-only
        tmpfs={'/tmp': 'rw,noexec,nosuid,size=64M'},
        cap_drop=['ALL'],
        security_opt=['no-new-privileges'],
        network_mode='bridge', # or 'host' if proxy needed, but bridge is safe
        mem_limit='256m',
        cpu_period=100000,
        cpu_quota=50000,
        environment={"NODE_OPTIONS": "--max-old-space-size=128"},
    )

    try:
        result = container.wait(timeout=30)
        logs = container.logs(stdout=True, stderr=True)
        output = logs.decode('utf-8').strip()
        # Find JSON line (last line that starts with '{')
        for line in output.splitlines():
            if line.startswith('{'):
                return json.loads(line)
        return {"error": "No valid JSON output", "raw": output}
    except Exception as e:
        return {"error": str(e)}