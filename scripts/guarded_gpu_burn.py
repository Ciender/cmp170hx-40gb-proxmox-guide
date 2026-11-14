#!/usr/bin/env python3
"""120 s gpu-burn with the tested 75 C temperature policy.

Publication copy: only GPU UUID, tool path and result path are externalized.
"""
# SPDX-License-Identifier: MIT
import csv
import ctypes as C
from datetime import datetime
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import threading
import time

OUT = Path(os.environ["CMP170HX_RESULT_DIR"]).resolve()
if sys.argv[1:] == ["--run"]:
    OUT.mkdir(parents=True, exist_ok=False)
REPO = Path(os.environ["GPU_BURN_REPO"]).resolve()
UUID = os.environ["CMP170HX_GPU_UUID"].encode("ascii")
STOP_C = 75
DURATION = 120

class Memory(C.Structure):
    _fields_ = [('total', C.c_ulonglong), ('free', C.c_ulonglong), ('used', C.c_ulonglong)]

class Utilization(C.Structure):
    _fields_ = [('gpu', C.c_uint), ('memory', C.c_uint)]

def limit_reason(sample, now):
    if sample is None or now - sample['monotonic'] > 1.0:
        return 'temperature telemetry missing or older than 1 second'
    if sample['temperature_c'] >= STOP_C:
        return f"core reached stop threshold: {sample['temperature_c']} C"
    if sample['power_limit_w'] != 150 or sample['enforced_power_limit_w'] != 150:
        return '150 W requested/enforced power limit no longer verified'
    return None

def kill_group(proc):
    if proc is not None:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

def main():
    # Exercise high-temperature, stale-monitor and power-limit decisions before load.
    fake = dict(monotonic=10, temperature_c=30, power_limit_w=150, enforced_power_limit_w=150)
    assert limit_reason(fake, 10) is None
    assert limit_reason(dict(fake, temperature_c=75), 10)
    assert limit_reason(fake, 11.1)
    assert limit_reason(dict(fake, enforced_power_limit_w=180), 10)
    harmless = subprocess.Popen(['sleep', '10'], start_new_session=True)
    kill_group(harmless)
    assert harmless.wait(timeout=2) == -signal.SIGKILL

    nvml = C.CDLL('libnvidia-ml.so.1')
    def bind(name, types):
        func = getattr(nvml, name)
        func.argtypes, func.restype = types, C.c_int
        return func
    def call(func, *args):
        code = func(*args)
        if code != 0:
            raise RuntimeError(f'{func.__name__} failed with NVML code {code}')
    init = bind('nvmlInit_v2', [])
    shutdown = bind('nvmlShutdown', [])
    handle_by_uuid = bind('nvmlDeviceGetHandleByUUID', [C.c_char_p, C.POINTER(C.c_void_p)])
    get_count = bind('nvmlDeviceGetCount_v2', [C.POINTER(C.c_uint)])
    get_temp = bind('nvmlDeviceGetTemperature', [C.c_void_p, C.c_uint, C.POINTER(C.c_uint)])
    get_power = bind('nvmlDeviceGetPowerUsage', [C.c_void_p, C.POINTER(C.c_uint)])
    get_limit = bind('nvmlDeviceGetPowerManagementLimit', [C.c_void_p, C.POINTER(C.c_uint)])
    get_enforced = bind('nvmlDeviceGetEnforcedPowerLimit', [C.c_void_p, C.POINTER(C.c_uint)])
    get_memory = bind('nvmlDeviceGetMemoryInfo', [C.c_void_p, C.POINTER(Memory)])
    get_util = bind('nvmlDeviceGetUtilizationRates', [C.c_void_p, C.POINTER(Utilization)])
    call(init)
    count, handle = C.c_uint(), C.c_void_p()
    call(get_count, C.byref(count))
    assert count.value == 1, 'Expected exactly one GPU'
    call(handle_by_uuid, UUID, C.byref(handle))
    state, lock, halt = {}, threading.Lock(), threading.Event()

    def sampler():
        try:
            while not halt.is_set():
                temp, power, limit, enforced = [C.c_uint() for _ in range(4)]
                mem, util = Memory(), Utilization()
                call(get_temp, handle, 0, C.byref(temp))
                call(get_power, handle, C.byref(power))
                call(get_limit, handle, C.byref(limit))
                call(get_enforced, handle, C.byref(enforced))
                call(get_memory, handle, C.byref(mem))
                call(get_util, handle, C.byref(util))
                sample = dict(timestamp=datetime.now().astimezone().isoformat(), monotonic=time.monotonic(),
                              temperature_c=temp.value, power_w=power.value / 1000,
                              power_limit_w=limit.value / 1000, enforced_power_limit_w=enforced.value / 1000,
                              memory_used_mib=mem.used / 1024**2, memory_total_mib=mem.total / 1024**2,
                              gpu_util_percent=util.gpu)
                with lock:
                    state['sample'] = sample
                halt.wait(0.25)
        except BaseException as exc:
            with lock:
                state['error'] = str(exc)

    thread = threading.Thread(target=sampler, daemon=True)
    thread.start()
    ready_until = time.monotonic() + 5
    while 'sample' not in state and 'error' not in state and time.monotonic() < ready_until:
        time.sleep(0.05)
    with lock:
        sample, sampler_error = state.get('sample'), state.get('error')
    reason = sampler_error or limit_reason(sample, time.monotonic())
    if reason:
        raise RuntimeError('Preflight refused GPU load: ' + reason)
    assert sample['memory_total_mib'] == 40960
    print(f"Preflight OK: {sample['temperature_c']} C, 40960 MiB, 150 W; stop at {STOP_C} C", flush=True)
    if sys.argv[1:] != ['--run']:
        halt.set()
        thread.join(timeout=1)
        call(shutdown)
        return

    command = ['stdbuf', '-oL', '-eL', './gpu_burn', '-i', '0', '-m', '90%', '-stts', '1', str(DURATION)]
    start = time.monotonic()
    samples, last, next_report, proc, reason = [], None, 0, None, None
    log_path = OUT / 'gpu-burn.log'
    (OUT / 'kernel-before-burn.log').write_text(subprocess.check_output(['journalctl', '-k', '-b', '--no-pager'], text=True))
    def interrupted(signum, frame):
        raise RuntimeError(f'monitor received signal {signum}')
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        with log_path.open('w') as gpu_log, (OUT / 'temperature.csv').open('w') as temperature_log:
            writer = csv.DictWriter(temperature_log, fieldnames=['elapsed_s'] + list(sample))
            writer.writeheader()
            proc = subprocess.Popen(command, cwd=REPO, stdout=gpu_log, stderr=subprocess.STDOUT, start_new_session=True)
            while True:
                now = time.monotonic()
                with lock:
                    sample, sampler_error = state.get('sample'), state.get('error')
                reason = sampler_error or limit_reason(sample, now)
                if reason:
                    kill_group(proc)
                if sample and sample['monotonic'] != last:
                    last = sample['monotonic']
                    row = dict(elapsed_s=round(now - start, 3), **sample)
                    samples.append(row)
                    writer.writerow(row)
                    temperature_log.flush()
                if reason:
                    raise RuntimeError(reason)
                if now - start >= next_report:
                    print(f"T+{now-start:.1f}s core={sample['temperature_c']} C power={sample['power_w']:.2f} W memory={sample['memory_used_mib']:.0f} MiB util={sample['gpu_util_percent']}%", flush=True)
                    next_report += 10
                text = log_path.read_text(errors='replace')
                if (any(int(n) for n in re.findall(r'errors:\s*(\d+)', text)) or
                    re.search(r'FAULTY|DIED!|Couldn.t init|No clients are alive|CUDA_ERROR|CUBLAS_STATUS', text)):
                    raise RuntimeError('gpu-burn reported an error; inspect gpu-burn.log')
                if proc.poll() is not None:
                    break
                if now - start > DURATION + 20:
                    raise RuntimeError('gpu-burn exceeded its allowed wall time')
                time.sleep(0.1)
        elapsed = time.monotonic() - start
        text = log_path.read_text(errors='replace')
        assert proc.returncode == 0, f'gpu-burn exited {proc.returncode}'
        assert elapsed >= DURATION - 1, f'gpu-burn ended early at {elapsed:.1f}s'
        assert re.search(r'GPU 0:\s*OK', text), 'Missing final GPU 0: OK'
        assert any(int(n) > 0 for n in re.findall(r"proc'd:\s*(\d+)", text)), 'No completed calculations'
        assert max(s['memory_used_mib'] for s in samples) > 32 * 1024, 'Expected more than 32 GiB allocated under load'
    except BaseException as exc:
        reason = str(exc)
        raise
    finally:
        kill_group(proc)
        if proc is not None:
            proc.wait(timeout=5)
        halt.set()
        thread.join(timeout=1)
        summary = dict(passed=reason is None, reason=reason, command=command, requested_duration_s=DURATION,
                       elapsed_s=round(time.monotonic() - start, 3), stop_threshold_c=STOP_C,
                       user_maximum_c=78, sample_period_s=0.25, samples=len(samples),
                       max_core_temperature_c=max((s['temperature_c'] for s in samples), default=None),
                       max_power_w=max((s['power_w'] for s in samples), default=None),
                       max_memory_used_mib=max((s['memory_used_mib'] for s in samples), default=None),
                       max_gpu_util_percent=max((s['gpu_util_percent'] for s in samples), default=None),
                       returncode=proc.returncode if proc is not None else None,
                       gpu_burn_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip())
        (OUT / 'gpu-burn-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
        print(json.dumps(summary, indent=2), flush=True)
        if not thread.is_alive():
            call(shutdown)

if __name__ == '__main__':
    main()
