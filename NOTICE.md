[![English](assets/lang-en-active.svg)](NOTICE.md) [![简体中文](assets/lang-zh.svg)](NOTICE.zh-CN.md)

# Sources, file attribution, and licenses

This repository records a successful reproduction. It does not implement a new NVIDIA driver or CMP unlock algorithm.

| File / content | Source | License |
| --- | --- | --- |
| Original documentation, data preparation, plotting, and offline verification tools | This reproduction | Root MIT license |
| `scripts/check_loaded_module.py`, topology check, 150 W helper, temperature monitor | Local helpers used in the measured run; published power/temperature copies externalize parameters, and the temperature copy also refuses to overwrite an existing result directory | Root MIT license |
| `third_party/cmp-gen2-watch/cmp-gen2-watch.c` | Johnnydaboy/cmpunlocker at `658110d5d1f15f7174d18f57caad4cab7d04593a`; the original file credits cmpunlocker PR #35 | GPL-2.0-only; see LICENSE in the same directory |
| `configs/host/cmp-gen2-watch.service` | Based on packaging/systemd/cmp-gen2-watch.service in Johnnydaboy/170hx-pve-gen2-controller at `9ba9da505f64d2c1a56703edc9516f42712ec7d9`, with this machine's topology ExecStartPre added | Apache-2.0; see third_party/licenses/Apache-2.0.txt |

Original project: [amoghmunikote/cmpunlocker](https://github.com/amoghmunikote/cmpunlocker). VFIO branch and dedicated guide: [Johnnydaboy/cmpunlocker](https://github.com/Johnnydaboy/cmpunlocker/tree/658110d5d1f15f7174d18f57caad4cab7d04593a). Companion deployment project: [Johnnydaboy/170hx-pve-gen2-controller](https://github.com/Johnnydaboy/170hx-pve-gen2-controller/tree/9ba9da505f64d2c1a56703edc9516f42712ec7d9).

The high WPR2 region reservation comes from upstream `f51da03`, credited to Amogh Munikote and co-contributors. The watcher source retains this branch's behavior of retiring a card after reaching its target. See the [source analysis](docs/SOURCE-ANALYSIS.md) for detailed attribution.

The NVIDIA base driver and gpu-burn were obtained from their respective repositories for the reproduction. Their binaries and full source trees are not bundled here. They remain subject to their own project licenses. Links to upstream projects, commits, and documentation do not change those licensing terms.
