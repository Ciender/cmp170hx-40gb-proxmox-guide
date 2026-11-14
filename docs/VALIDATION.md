[![English](../assets/lang-en-active.svg)](VALIDATION.md) [![简体中文](../assets/lang-zh.svg)](VALIDATION.zh-CN.md)

# Successful run and evidence index

Validation date: 2026-11-14. This report covers the final successful pinned branch, configuration, and measured results. See the [README](../README.md) for the procedure and the [source analysis](SOURCE-ANALYSIS.md) for mechanisms and attribution.

## Verification order

After a full cold power cycle, the guest's first initialization log was preserved and the loaded GNU build ID checked. The physical PVE BAR and link state were inspected next. Temperature-monitored gpu-burn started only after initialization, persistence, and the 150 W limit were verified. After the test, checks covered process cleanup, GPU state, and guest/host kernel errors.

Evidence directory: [evidence/2026-11-14](../evidence/2026-11-14/).

| Check | Result | Evidence |
| --- | --- | --- |
| Pinned source, base archive, and modules | 610.43.02, seven default patches, five modules built successfully | [build-manifest.json](../evidence/2026-11-14/build-manifest.json) |
| Loaded image matches the installed module | GNU build ID, SHA256, and srcversion recorded | [loaded-module.json](../evidence/2026-11-14/loaded-module.json) |
| Installed driver libraries / firmware | 610.43.02-1 | [userspace-packages.txt](../evidence/2026-11-14/userspace-packages.txt) |
| Signature restoration, 40GB geometry, WPR2 reservation | Log matches the pinned branch's successful path | [guest-kernel-success.log](../evidence/2026-11-14/guest-kernel-success.log) |
| Physical host link, BAR1, VFIO, and idle D3 | Gen2 ×4, consistent 64 MiB BAR1, vfio-pci, Y | [host-verification.json](../evidence/2026-11-14/host-verification.json) |
| Window detection and watcher retirement | Detected at T+43.135, Gen2 reached at T+43.136 | [host-gen2-watch.log](../evidence/2026-11-14/host-gen2-watch.log) |
| gpu-burn computation checks | 0 errors, GPU 0: OK | [gpu-burn.log](../evidence/2026-11-14/gpu-burn.log) |
| All temperature, power, and memory samples | 525 samples, maximum core temperature 53°C | [temperature.csv](../evidence/2026-11-14/temperature.csv) |
| Machine-readable stress-test result | 120-second argument, 131.451-second wall time | [gpu-burn-summary.json](../evidence/2026-11-14/gpu-burn-summary.json) |
| CUDA properties and post-test guest checks | 70 SMs, CC 8.0, empty error list, no remaining load process | [post-test-verification.json](../evidence/2026-11-14/post-test-verification.json) |
| Post-test host error screening | No matching AER/VFIO/DMAR errors | [host-kernel-check.json](../evidence/2026-11-14/host-kernel-check.json) |
| Post-test GPU state | 40960 MiB, Gen2 ×4, 150 W, 32°C | [gpu-after-burn.csv](../evidence/2026-11-14/gpu-after-burn.csv) |

## Interpreting the measurements

### Memory

- **40960 MiB**: total framebuffer capacity reported by NVML.
- **40483.625 MiB**: CUDA driver API's visible total, accounting for different reservations.
- **36161 MiB**: the capacity gpu-burn reported it would use at initialization, approximately 35.31 GiB.
- **36876.3125 MiB**: peak NVML total memory usage during monitoring, which includes more than gpu-burn's own allocation.

These measurements establish that the workload used substantially more than the stock 10GB and completed computation checks. They do not replace a dedicated memory test that writes and reads unique patterns at every allocatable address. Firmware-reserved space was not tested.

### Duration and calculations

gpu-burn was invoked with `120` seconds. The monitor recorded **131.451 seconds** of total wall time, including CUDA/buffer initialization and shutdown. Each matrix result occupied 268435456 bytes, with 139 matrix multiplications per iteration batch and 1112 reported in total. Neither this count nor the initialization time establishes long-duration stability.

### Temperature and power

NVML was sampled approximately every 0.25 seconds, producing 525 samples. Core temperature peaked at **53°C**. The software early-stop threshold was **75°C**, with a required core-temperature ceiling of **78°C**. No temperature stop was triggered.

Requested and enforced power limits were **150 W** in all recorded samples. Peak instantaneous power draw was **154.659 W**. This is the measured value from the complete telemetry; the 150 W setting is not presented as an absolute cap on every instantaneous reading.

The first GPU-state query after completion reported **32°C** and **28.76 W**. No `gpu_burn` process remained.

## Scope not covered by this run

There was no long-duration aging test, repeated cold-boot study, full-address memory test, multi-card workload, ECC test, additional 4 SM test, alternative power-limit test, other motherboard test, or BAR1-size performance comparison. The upstream author's dual-card 8GB results remain the author's separate results and are not counted as local runs.

Host/guest Secure Boot EFI state and individual BIOS menu settings were not independently read. The verified observations are successful module loading, working IOMMU/VFIO, BAR addresses above 4 GiB, and runtime behavior. The existing 512 GiB PCI hole and 256 GiB OVMF MMIO window were retained; minimum required sizes were not measured.

## Publication handling

Measured values, timestamps, PCI addresses, and build hashes were retained. GPU UUIDs were replaced with `GPU-REDACTED`, hostnames with generic labels, and log line endings normalized. Boot IDs, SSH credentials, private addresses, and the original work directory were excluded. The published kernel log is an excerpt of the successful path; error-screening results are supplied separately as JSON. The excerpt is not a complete system log.

`python3 tools/verify_evidence.py` checks the final OK result, all reported error counts, telemetry count, temperature peak, 150 W settings, memory usage, host checks, and local document links offline. It does not access a GPU or restart a workload.
