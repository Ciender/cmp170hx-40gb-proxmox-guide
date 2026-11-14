#!/usr/bin/python3
"""Apply and verify this card's 150 W limit; fail if NVML cannot see it."""
# SPDX-License-Identifier: MIT
import csv
import os
import subprocess
import sys
import time

GPU = os.environ["CMP170HX_GPU_UUID"]


def smi(*args):
    result = subprocess.run(
        ["/usr/bin/nvidia-smi", *args],
        check=True, text=True, capture_output=True, timeout=30,
    )
    return result.stdout.strip()


try:
    devices = smi("--query-gpu=uuid", "--format=csv,noheader").splitlines()
    if GPU not in devices:
        raise RuntimeError(f"Target GPU is absent: {GPU}")
    smi("-i", GPU, "-pm", "1")
    smi("-i", GPU, "-pl", "150")
    for attempt in range(2):
        if attempt:
            time.sleep(2)
        report = smi(
            "-i", GPU,
            "--query-gpu=uuid,persistence_mode,power.limit,enforced.power.limit",
            "--format=csv,noheader,nounits",
        )
        rows = list(csv.reader(report.splitlines(), skipinitialspace=True))
        if len(rows) != 1 or len(rows[0]) != 4:
            raise RuntimeError(f"Unexpected power report: {report!r}")
        uuid, persistence, requested, enforced = rows[0]
        if (uuid != GPU or persistence != "Enabled"
                or float(requested) != 150.0 or float(enforced) != 150.0):
            raise RuntimeError(f"Power limit verification failed: {report}")
        print(report, flush=True)
except (subprocess.SubprocessError, RuntimeError, ValueError) as error:
    print(f"150 W power limit NOT verified: {error}", file=sys.stderr)
    sys.exit(1)
