[![English](../assets/lang-en-active.svg)](SOURCE-ANALYSIS.md) [![简体中文](../assets/lang-zh.svg)](SOURCE-ANALYSIS.zh-CN.md)

# Source fixes and attribution for the successful path

This document explains why this combination was used, based on the pinned local source. It distinguishes code behavior, the author's explanations, and observations from this run. The complete procedure is in the [README](../README.md).

## 1. The pinned revision

This run used [Johnnydaboy/cmpunlocker at `658110d`](https://github.com/Johnnydaboy/cmpunlocker/tree/658110d5d1f15f7174d18f57caad4cab7d04593a). The directly relevant history includes:

| Commit | Author / source | Purpose |
| --- | --- | --- |
| [`209d4a48588087f4e0cf3087f974ff70593d8505`](https://github.com/Johnnydaboy/cmpunlocker/commit/209d4a48588087f4e0cf3087f974ff70593d8505) | Jonathan / Johnnydaboy | `Fix dual CMP 170HX unlock under Proxmox VFIO`: changes the default patch set, signature restoration, WPR2 handling, GSP initialization, and related Gen2 writes |
| [`658110d5d1f15f7174d18f57caad4cab7d04593a`](https://github.com/Johnnydaboy/cmpunlocker/commit/658110d5d1f15f7174d18f57caad4cab7d04593a) | Jonathan / Johnnydaboy | Adds the reproducible dual-CMP Proxmox deployment guide |
| [`f51da030ef4260656288edf07e95ae45f339aea8`](https://github.com/Johnnydaboy/cmpunlocker/commit/f51da030ef4260656288edf07e95ae45f339aea8) | Original upstream, Amogh Munikote and co-contributors | Keeps the high memory region reserved so WPR2 storage is not returned to the ordinary allocator |

`f51da03` is an upstream fix included in this branch. It was not written during this reproduction, and its contribution should not all be attributed to Johnny.

## 2. BAR1: separate framebuffer capacity from the PCI aperture

Source: [driver/build.sh](https://github.com/Johnnydaboy/cmpunlocker/blob/658110d5d1f15f7174d18f57caad4cab7d04593a/driver/build.sh).

The default patch array excludes `bar1-resize-unlock.patch`. It is appended only when `CMPUNLOCKER_ENABLE_BAR1_RESIZE=1` is explicitly set. This run used `0`.

Two layers must remain consistent: the GPU's physical BAR1 size is hardware state, while the guest PCI aperture and VFIO mapping are established by PVE/QEMU. If a guest driver changes the physical BAR through GPU registers after VM creation while QEMU retains the original mapping size, the layers can disagree. The dedicated upstream guide links that disagreement to BAR2/MMU initialization failures.

Measured state in the successful boot:

| Layer | BAR1 / memory value |
| --- | --- |
| GPU Physical Resizable BAR | Current size: 64 MiB |
| PVE GPU resource 1 | `0xd2ff8000000–0xd2ffbffffff`, 64 MiB |
| GPU configuration-space BAR1 base | Matches PVE resource 1 |
| Guest resource 1 | `0x380800000000–0x380803ffffff`, 64 MiB |
| NVML framebuffer capacity | 40960 MiB |
| gpu-burn memory allocated for computation | 36161 MiB |

Different host and guest base addresses are normal because they belong to different address spaces. The checks compare the physical state and mapping sizes at the relevant layer; they do not require host and guest base addresses to be numerically identical.

The measured conclusion is that **this 40GB unlock and a compute workload using substantially more than the stock 10GB work with a 64 MiB BAR1 aperture**. This machine was not benchmarked across different BAR1 sizes, and the result is not a compatibility claim for every driver and platform.

## 3. Signature storage: allocation size is not signature length

Source: [sec2-postbl-plm-ss-cfg.patch](https://github.com/Johnnydaboy/cmpunlocker/blob/658110d5d1f15f7174d18f57caad4cab7d04593a/driver/patches/sec2-postbl-plm-ss-cfg.patch).

The patch saves the stock signature in `pStockSignatureData` / `stockSignatureSize` and keeps a larger signature memory descriptor for the exploit. These are different quantities:

| Quantity | Value / purpose in this run |
| --- | --- |
| Actual stock GSP signature length | 4096 bytes |
| Buffer allocated for the exploit stage | `0xf800`, about 62 KiB |

Johnny's fix restores the stock signature inside the existing descriptor instead of destroying it and creating a new descriptor only 4096 bytes long. It clears the buffer, copies the original signature, and flushes caches. When WPR metadata is populated again, the code explicitly restores the equivalent of `sizeOfSignature = stockSignatureSize`, so the exploit buffer's full allocation size is not treated as the valid signature length.

The author's guide associates the wrong length with Booter `0xb`. The successful log here directly records:

```text
saved stock signature (4096 bytes)
WPR meta updated fbSize=0x0000000a00000000 ... sigSize=4096
```

This verifies the current successful path. No additional failure injection was performed, and the result is not a formal safety proof for every exceptional retry path.

## 4. WPR2: restoring hardware bounds and retaining allocator reservations

Before the SEC2 writes, the patch saves the WPR2 registers. After the writes and memory-geometry update, it restores those values to `0x001fa824` and `0x001fa828`. The associated WPR metadata descriptor is flushed.

The saved and restored values in this run were:

```text
WPR2 lo=0x1ffffe00 hi=0x00000000
```

These values show restoration of the saved hardware state; that line alone is not the final 40GB WPR interval. The later metadata gives:

```text
fbSize   = 0x0000000a00000000
wprStart = 0x00000009f7600000
wprEnd   = 0x00000009fff00000
```

Separately, [late-pma.patch](https://github.com/Johnnydaboy/cmpunlocker/blob/658110d5d1f15f7174d18f57caad4cab7d04593a/driver/patches/late-pma.patch) retains upstream `f51da03` behavior: keep the region traversal and diagnostic output, but do not re-register the high reserved region with PMA.

Measured output:

```text
candidate=6 base=0x9f7500000 limit=0x9ffffffff left reserved (backs WPR2)
```

This approximately 139 MiB region overlaps WPR2-related storage. Keeping it reserved reduces the capacity available to ordinary allocations but avoids allocating over live firmware. Reclaiming it just to make the free-memory figure closer to NVML's total would defeat that protection.

## 5. Initialization: retain locking and exclude unnecessary paths

In `_kgspShouldRelaxGspInitLocking`, the patch returns `NV_FALSE` for the two target CMP IDs, keeping initialization under the existing lock. The author used this to address parallel GSP initialization timing on a dual-card Q35/VFIO system. This reproduction has one card and does not independently verify that dual-card race.

The default `driver/build.sh` set excludes:

- `booter-verify.patch`;
- `pcie-gen2-probe-retrain.patch`;
- `bar1-resize-unlock.patch`, unless explicitly enabled.

This run kept that default set instead of adding patches to reproduce every feature listed in the general README.

## 6. Gen2: the guest prepares the endpoint, the host retrains its physical parent

Sources: [pcie-gen2.patch](https://github.com/Johnnydaboy/cmpunlocker/blob/658110d5d1f15f7174d18f57caad4cab7d04593a/driver/patches/pcie-gen2.patch) and [cmp-gen2-watch.c](https://github.com/Johnnydaboy/cmpunlocker/blob/658110d5d1f15f7174d18f57caad4cab7d04593a/tools/cmp-gen2-watch.c).

### Remove the ECC PLM write unrelated to Gen2

`209d4a4` removes the following entry from the Gen2 register table:

```text
address: 0x00823800
label:   FEAT_OVR_ECC_PLM
```

The author's dedicated guide identifies this write as the precise transition from expected `0x31` to fatal `0x15` on the author's second GPU. That is the author's diagnosis. This reproduction used the source with the write removed and passed initialization and computation; the write was not re-enabled for a comparison run.

### Retrain the physical link during the advertisement window

The original watcher source reports a roughly 430 ms Gen2 advertisement window on some combinations. That duration is the author's observation recorded in the source. This machine verified that the window was caught and Gen2 succeeded, without independently measuring the window's duration.

The watcher:

1. Discovers supported `10de:20c2 / 2082` GPUs.
2. Walks sysfs topology to a real root/downstream port capable of retraining.
3. Polls the endpoint's LnkCap at a nominal 1 ms interval.
4. Sets the parent's Target Link Speed and writes Retrain Link when the target capability appears.
5. Checks link status and retires each card from further retraining after reaching the target.

The source credits cmpunlocker PR #35 and records the branch's addition of retiring cards once the target is reached. The file vendored here is the original file from that branch, with the same SHA256 as the source compiled on PVE in this run.

This topology was `51:00.0 → 50:02.0`, with the following measured log:

```text
T+43.135 ... LnkCap 00456101 -> 00456102
T+43.135 ... retrain via 0000:50:02.0
T+43.136 ... trained at Gen2; retiring watcher for this card
```

`T+` is the watcher's own relative timer, not an exact timestamp since system power-on. The final link was Gen2 ×4 in both PVE and the guest.

## 7. What was adapted locally

| Component | Treatment in this reproduction |
| --- | --- |
| Seven driver patches | Original files from the pinned branch, without local driver-code changes |
| NVIDIA base source | Tag `610.43.02`, archive SHA256 verified |
| 10GB configuration | profile=10gb, one-card inventory, target 40960 MiB; runtime geometry selected by PCI ID 2082 |
| Debian headers | make variables specify separate source and output directories |
| Installation timing | `CMPUNLOCKER_SKIP_RELOAD=1`, followed by a cold power cycle |
| Host watcher | Original upstream C source |
| Host unit | Based on the companion unit, with a pre-start topology check for this single card |
| Host VFIO | Added early 2082 binding and disable_idle_d3=1 while preserving other devices |
| VM | Enabled onboot to start within the watcher window; retained existing MMIO settings |
| Power service | UUID-based single-card 150 W helper rather than the author's dual-card 180 W example |
| Stress test | Pinned gpu-burn with core-temperature sampling and early-stop protection |

The result is **an adaptation of the upstream VFIO path to this single 2082 card, verified through boot, physical link state, CUDA properties, and a short compute stress test**. It does not claim a new unlock implementation or compatibility validation for all CMP 170HX cards, BIOS versions, or virtualization platforms.
