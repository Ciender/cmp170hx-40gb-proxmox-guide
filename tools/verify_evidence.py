#!/usr/bin/env python3
"""Validate the published experiment offline. Never imports GPU libraries."""
import csv
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'evidence/2026-11-14'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(name):
    return json.loads((DATA / name).read_text())


def verify():
    summary = read_json('gpu-burn-summary.json')
    post = read_json('post-test-verification.json')
    host = read_json('host-verification.json')
    manifest = read_json('build-manifest.json')
    samples = list(csv.DictReader((DATA / 'temperature.csv').open()))
    burn = (DATA / 'gpu-burn.log').read_text()

    require(summary['passed'] is True and summary['returncode'] == 0, 'gpu-burn was not successful')
    require(summary['requested_duration_s'] == 120, 'Unexpected test duration')
    require(abs(summary['elapsed_s'] - 131.451) < 0.001, 'Unexpected measured wall time')
    require(len(samples) == summary['samples'] == 525, 'Telemetry sample count mismatch')
    require(re.search(r'GPU 0:\s*OK', burn), 'Missing final GPU 0: OK')
    errors = [int(n) for n in re.findall(r'errors:\s*(\d+)', burn)]
    require(errors and not any(errors), 'Missing error reports or nonzero gpu-burn errors')
    require(not re.search(r'FAULTY|DIED!|Couldn.t init|No clients are alive', burn), 'gpu-burn failure text found')
    allocated = re.search(r'using (\d+) MB of it', burn)
    require(allocated and int(allocated[1]) == 36161, 'Memory allocation mismatch')
    require(max(int(n) for n in re.findall(r"proc'd:\s*(\d+)", burn)) == 1112, 'Calculation count mismatch')

    maximum_temp = max(float(s['temperature_c']) for s in samples)
    require(maximum_temp == summary['max_core_temperature_c'] == 53, 'Temperature peak mismatch')
    require(all(float(s['temperature_c']) < 75 for s in samples), '75 C early-stop threshold reached')
    require(all(float(s['memory_total_mib']) == 40960 for s in samples), 'Framebuffer total changed')
    require(all(float(s['power_limit_w']) == float(s['enforced_power_limit_w']) == 150 for s in samples), '150 W limit changed')
    require(max(float(s['memory_used_mib']) for s in samples) == summary['max_memory_used_mib'] == 36876.3125, 'Memory usage peak mismatch')
    require(abs(max(float(s['power_w']) for s in samples) - 154.659) < 0.0001, 'Power peak mismatch')
    require(max(float(s['gpu_util_percent']) for s in samples) == 100, 'Full GPU utilization not recorded')
    times = [float(s['monotonic']) for s in samples]
    require(all(0 < b - a < 1 for a, b in zip(times, times[1:])), 'Invalid or missing telemetry interval')

    require(all(host['checks'].values()), 'A physical host check failed')
    require(host['gpu']['driver'] == 'vfio-pci', 'Incorrect host GPU driver')
    require(host['vfio_disable_idle_d3'] == 'Y', 'VFIO idle D3 is not disabled')
    for device in (host['gpu'], host['parent']):
        require(device['link_speed'].startswith('5.0 GT/s') and device['link_width'] == '4', 'Physical Gen2 x4 missing')
    bar1 = host['gpu']['resources'][1]
    bar3 = host['gpu']['resources'][3]
    require(bar1['bytes'] == 64 * 1024**2, 'BAR1 size mismatch')
    require(int(bar1['end'], 16) < int(bar3['start'], 16), 'BAR1 overlaps BAR3')
    require('all cards reached Gen2' in host['watcher_log_tail'], 'Missing successful watcher exit')

    require(not post['kernel_gpu_failures'] and not post['gpu_burn_processes_remaining'], 'Post-test failure recorded')
    require(not read_json('host-kernel-check.json')['kernel_relevant_failures'], 'Host kernel error recorded')
    require(post['cuda_properties']['multiprocessor_count'] == 70, 'SM count mismatch')
    require(post['cuda_properties']['cuda_usable_total_mib'] == 40483.625, 'CUDA total mismatch')
    require(post['gpu_burn'] == summary, 'Summary copies differ')
    modules = manifest['modules']
    require(len(modules) == 5 and len(manifest['active_patches']) == 7, 'Module or patch count mismatch')
    require(manifest['commit'] == '658110d5d1f15f7174d18f57caad4cab7d04593a', 'Driver source commit mismatch')
    loaded = read_json('loaded-module.json')
    main_module = next(m for m in modules if m['file'] == 'nvidia.ko')
    require(loaded['match'] and loaded['gpu_accessed'] is False, 'Loaded module identity not verified')
    require(loaded['loaded_build_id'] == loaded['installed_build_id'] == main_module['build_id'], 'Loaded and built module IDs differ')
    require(loaded['installed_sha256'] == main_module['sha256'], 'Installed and built module hashes differ')
    packages = (DATA / 'userspace-packages.txt').read_text().splitlines()
    require(len(packages) == 24 and all(line.endswith(' 610.43.02-1') for line in packages), 'Package version mismatch')

    source = ROOT / 'third_party/cmp-gen2-watch/cmp-gen2-watch.c'
    require(hashlib.sha256(source.read_bytes()).hexdigest() == 'd39d2b76dfac1b63c8af9efe7857055c3f5d1873184f8b3eea1aaa7d0304710e', 'Vendored watcher differs from tested upstream')
    require((ROOT / 'assets/gpu-burn-telemetry.png').is_file(), 'Missing telemetry plot')
    checksum_file = DATA / 'SHA256SUMS'
    require(checksum_file.exists(), 'Missing evidence checksums')
    for line in checksum_file.read_text().splitlines():
        digest, relative = line.split('  ', 1)
        item = (DATA / relative).resolve()
        require(item.is_relative_to(DATA), 'Checksum path leaves evidence directory')
        require(hashlib.sha256(item.read_bytes()).hexdigest() == digest, f'Checksum mismatch: {relative}')

    missing = []
    for doc in ROOT.rglob('*.md'):
        if '.git' in doc.parts:
            continue
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', doc.read_text()):
            target = target.strip('<>')
            parsed = urlsplit(target)
            if parsed.scheme or not parsed.path:
                continue
            path = unquote(parsed.path)
            linked = (doc.parent / path).resolve()
            if path.startswith('/') or not linked.is_relative_to(ROOT) or not linked.exists():
                missing.append(f'{doc.relative_to(ROOT)}: {target}')
    require(not missing, 'Invalid local Markdown links:\n' + '\n'.join(missing))

    # Real device UUIDs and private network addresses are unnecessary in a public case study.
    private = re.compile(r'GPU-[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}|\b192\.168\.\d+\.\d+\b|\b10\.\d+\.\d+\.\d+\b')
    for path in ROOT.rglob('*'):
        if not path.is_file() or '.git' in path.parts or '__pycache__' in path.parts or path.suffix in ('.png', '.pyc'):
            continue
        require(not private.search(path.read_text()), f'Unredacted private identifier: {path.relative_to(ROOT)}')
    print('PASS: 40 GiB framebuffer, physical Gen2 x4, BAR1 64 MiB, 150 W limits.')
    print('PASS: gpu-burn 120 s, 36161 MiB allocation, zero errors, maximum core 53 C.')
    print('PASS: 525 telemetry samples, source hash, evidence checksums, links and redaction.')


if __name__ == '__main__':
    try:
        verify()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        raise SystemExit(1)
