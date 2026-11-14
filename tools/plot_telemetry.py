#!/usr/bin/env python3
"""Render the published measurements; requires matplotlib, never accesses a GPU."""
import csv
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
with (ROOT / 'evidence/2026-11-14/temperature.csv').open() as stream:
    rows = list(csv.DictReader(stream))
t = [float(r['elapsed_s']) for r in rows]
temp = [float(r['temperature_c']) for r in rows]
power = [float(r['power_w']) for r in rows]
memory = [float(r['memory_used_mib']) / 1024 for r in rows]

plt.rcParams.update({'font.size': 10, 'axes.spines.top': False,
                     'axes.spines.right': False, 'figure.facecolor': 'white'})
fig, axes = plt.subplots(3, 1, figsize=(10, 8.5), sharex=True, constrained_layout=True)
fig.suptitle('CMP 170HX | 40 GiB | Gen2 x4 | 150 W limit\n'
             'gpu-burn: 120 s requested, 0 errors, GPU 0: OK', fontsize=15, weight='bold')
axes[0].plot(t, temp, color='#147a67', lw=2, label='GPU core temperature')
axes[0].axhline(75, color='#bd7610', ls='--', lw=1.3, label='Software stop: 75 C')
axes[0].axhline(78, color='#b52b38', ls=':', lw=1.5, label='User ceiling: 78 C')
axes[0].set_ylim(20, 83)
axes[0].set_ylabel('Core temperature (C)')
peak_index = temp.index(max(temp))
axes[0].annotate(f'Maximum: {max(temp):.0f} C', (t[peak_index], temp[peak_index]),
                 xytext=(-45, -30), textcoords='offset points',
                 arrowprops={'arrowstyle': '->', 'color': '#147a67'}, color='#147a67')
axes[0].legend(loc='upper left', fontsize=9)
axes[1].plot(t, power, color='#3465a4', lw=1.2, label='Sampled power draw')
axes[1].axhline(150, color='#bd7610', ls='--', lw=1.2, label='Requested/enforced limit: 150 W')
axes[1].set_ylim(15, 170)
axes[1].set_ylabel('Power (W)')
axes[1].legend(loc='lower right', fontsize=9)
axes[2].plot(t, memory, color='#7856a5', lw=1.8, label='NVML total memory used')
axes[2].fill_between(t, memory, color='#7856a5', alpha=0.1)
axes[2].axhline(40, color='#707070', ls='--', lw=1.2, label='NVML framebuffer: 40 GiB')
axes[2].set_ylim(0, 44)
axes[2].set_ylabel('Memory (GiB)')
axes[2].set_xlabel('Elapsed wall time including initialization / shutdown (s)')
axes[2].legend(loc='lower right', fontsize=9)
for ax in axes:
    ax.set_xlim(0, t[-1])
    ax.grid(True, color='#dce2e8', alpha=0.75, lw=0.6)
fig.savefig(ROOT / 'assets/gpu-burn-telemetry.png', dpi=170)
plt.close(fig)
print('Rendered assets/gpu-burn-telemetry.png from', len(rows), 'samples')
