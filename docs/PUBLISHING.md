[![English](../assets/lang-en-active.svg)](PUBLISHING.md) [![简体中文](../assets/lang-zh.svg)](PUBLISHING.zh-CN.md)

# Getting, checking, and maintaining the repository

Public repository: [Ciender/cmp170hx-40gb-proxmox-guide](https://github.com/Ciender/cmp170hx-40gb-proxmox-guide). The default branch is `main`. The default README is English; use the language buttons at the top of each guide to switch to Simplified Chinese.

## 1. Get the documentation and configuration

```bash
git clone https://github.com/Ciender/cmp170hx-40gb-proxmox-guide.git
cd cmp170hx-40gb-proxmox-guide
```

You can also choose Code → Download ZIP on GitHub. The repository home page renders the root README, with relative links to plots, source analysis, configuration templates, and redacted evidence.

## 2. Verify offline

```bash
python3 tools/verify_evidence.py
python3 -m compileall -q scripts tools
cc -O2 -Wall -Wextra -o /tmp/cmp-gen2-watch third_party/cmp-gen2-watch/cmp-gen2-watch.c
```

These checks do not start a GPU workload or run the watcher. Commands that operate on hardware in the guide are labeled PVE or guest. Adapt the example addresses to the actual topology before reproducing the setup.

The repository does not contain driver packages, compiled kernel modules, or complete system backups. Obtain the NVIDIA source and gpu-burn from the upstream revisions pinned in the README.

## 3. Maintainer updates

With a GitHub account that has write access, verify the evidence before committing:

```bash
python3 tools/verify_evidence.py
git diff --check
git add .
git commit -m "Update the CMP 170HX reproduction guide"
git push origin main
```

The successful run is stored under `evidence/2026-11-14/` with a SHA256 manifest. Put future experiments in a new dated directory, state their conditions, and preserve existing raw data. Text-only documentation updates do not require rerunning GPU stress tests.

Keep corresponding English and Chinese guides aligned. In particular, preserve pinned revisions, commands, measurements, attribution, and validation limits in both languages.

`.github/workflows/validate.yml` runs offline evidence verification, Python syntax checks, and watcher compilation on pushes and pull requests. It does not require a GPU runner.

## 4. Sources and licenses

The root MIT license covers original documentation and helper scripts. The upstream watcher retains GPLv2, and the third-party unit retains Apache-2.0 attribution; see [NOTICE](../NOTICE.md). The [source analysis](SOURCE-ANALYSIS.md) distinguishes upstream driver fixes from this machine's environment adaptations.
