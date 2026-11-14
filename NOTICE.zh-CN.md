[![English](assets/lang-en.svg)](NOTICE.md) [![简体中文](assets/lang-zh-active.svg)](NOTICE.zh-CN.md)

# 来源、文件归属与许可证

本仓库用于记录成功复现，没有重新实现 NVIDIA 驱动或 CMP 解锁算法。

| 文件 / 内容 | 来源 | 许可证 |
| --- | --- | --- |
| 原创文档、数据整理、绘图及离线核验工具 | 本次复现记录 | 根目录 MIT |
| `scripts/check_loaded_module.py`、拓扑检查、150W helper、温控 helper | 本次实测使用的本地辅助脚本；功率与温控副本外置参数，温控副本另拒绝覆盖现有输出目录 | 根目录 MIT |
| `third_party/cmp-gen2-watch/cmp-gen2-watch.c` | Johnnydaboy/cmpunlocker，提交 `658110d5d1f15f7174d18f57caad4cab7d04593a`，原文件注明基于 cmpunlocker PR #35 | GPL-2.0-only，见同目录 LICENSE |
| `configs/host/cmp-gen2-watch.service` | 基于 Johnnydaboy/170hx-pve-gen2-controller，提交 `9ba9da505f64d2c1a56703edc9516f42712ec7d9` 的 packaging/systemd/cmp-gen2-watch.service，增加本机拓扑 ExecStartPre | Apache-2.0，见 third_party/licenses/Apache-2.0.txt |

原始项目：[amoghmunikote/cmpunlocker](https://github.com/amoghmunikote/cmpunlocker)。VFIO 分支及专用文档：[Johnnydaboy/cmpunlocker](https://github.com/Johnnydaboy/cmpunlocker/tree/658110d5d1f15f7174d18f57caad4cab7d04593a)。配套部署项目：[Johnnydaboy/170hx-pve-gen2-controller](https://github.com/Johnnydaboy/170hx-pve-gen2-controller/tree/9ba9da505f64d2c1a56703edc9516f42712ec7d9)。

高端 WPR2 区域保留来自分支包含的上游 `f51da03`，署名为 Amogh Munikote 及其共同贡献者。watcher 的退役行为由该分支保留在源码中。详细归属见 [源码说明](docs/SOURCE-ANALYSIS.zh-CN.md)。

NVIDIA 基础驱动和 gpu-burn 在复现时从各自仓库获取，本发布目录没有打包它们的二进制或完整源码。它们仍按各自项目许可证分发。本文链接到的上游项目、提交及文档均不因本仓库根许可证而改变许可条件。
