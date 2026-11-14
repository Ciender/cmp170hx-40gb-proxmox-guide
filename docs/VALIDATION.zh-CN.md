# 本次成功结果与证据索引

验证日期：2026-11-14。这里仅记录最后成功的固定分支、配置与运行结果。操作过程见 [README](../README.md)，机制和贡献归属见 [源码说明](SOURCE-ANALYSIS.zh-CN.md)。

## 验证顺序

完整冷启动后，先保存 guest 首次内核日志、核对实际加载的 GNU build ID，再检查 PVE 的物理 BAR 与链路。初始化正常且 persistence / 150W 已生效后，才启动温控 gpu-burn。测试结束后检查进程退出、GPU 状态以及 guest/host 内核错误。

证据目录：[evidence/2026-11-14](../evidence/2026-11-14/)。

| 验证项 | 结果 | 对应文件 |
| --- | --- | --- |
| 固定上游、基础源码及模块 | 610.43.02，七默认补丁，五模块构建成功 | [build-manifest.json](../evidence/2026-11-14/build-manifest.json) |
| 实际加载与磁盘模块的身份一致 | GNU build ID、SHA256、srcversion | [loaded-module.json](../evidence/2026-11-14/loaded-module.json) |
| 实际驱动库 / 固件包 | 610.43.02-1 | [userspace-packages.txt](../evidence/2026-11-14/userspace-packages.txt) |
| 签名恢复、40GB 几何、WPR2 保留 | 日志符合固定分支的成功路径 | [guest-kernel-success.log](../evidence/2026-11-14/guest-kernel-success.log) |
| host 物理链路、BAR1、VFIO、D3 参数 | Gen2 ×4、64MiB、一致、vfio-pci、Y | [host-verification.json](../evidence/2026-11-14/host-verification.json) |
| 窗口捕捉及 watcher 退役 | T+43.135 捕捉，T+43.136 成功 | [host-gen2-watch.log](../evidence/2026-11-14/host-gen2-watch.log) |
| gpu-burn 计算校验 | 0 错误，GPU 0: OK | [gpu-burn.log](../evidence/2026-11-14/gpu-burn.log) |
| 全部温度、功耗和显存采样 | 525 个样本，核心最高 53℃ | [temperature.csv](../evidence/2026-11-14/temperature.csv) |
| 压测机器可读结果 | 120 秒参数，131.451 秒 wall time | [gpu-burn-summary.json](../evidence/2026-11-14/gpu-burn-summary.json) |
| CUDA 属性及测试后 guest 故障筛查 | 70 SM、CC 8.0、错误列表为空、无残留负载进程 | [post-test-verification.json](../evidence/2026-11-14/post-test-verification.json) |
| 测试后 host 错误筛查 | 匹配到的 AER/VFIO/DMAR 错误为空 | [host-kernel-check.json](../evidence/2026-11-14/host-kernel-check.json) |
| 测试后 GPU 状态 | 40960MiB、Gen2 ×4、150W、32℃ | [gpu-after-burn.csv](../evidence/2026-11-14/gpu-after-burn.csv) |

## 数值如何解释

### 显存

- **40960MiB**：NVML 报告的总 framebuffer 容量。
- **40483.625MiB**：CUDA driver API 报告的可见总容量，包含保留空间差异。
- **36161MiB**：gpu-burn 初始化时报告准备使用的容量，约 35.31GiB。
- **36876.3125MiB**：监控期间 NVML 总显存占用峰值，计入范围比 gpu-burn 的单项分配更广。

这组证据证明负载使用了显著超过原始 10GB 的容量并完成计算校验。它不能替代一个对全部可分配地址做唯一模式写入和回读的显存专测，也没有覆盖保留给固件的区域。

### 时间和计算量

gpu-burn 参数为 `120` 秒。监控器记录的总 wall time 是 **131.451 秒**，包含 CUDA/缓冲初始化和退出过程。输出中矩阵结果单份为 268435456 bytes，每轮 139 次矩阵乘法，报告累计完成 1112 次；不能把初始化时间或该计算量改写为长期稳定性结果。

### 温度和功率

每约 0.25 秒采样一次 NVML，实际保存 525 个样本。核心最高 **53℃**；本次软件停止阈值 **75℃**，用户核心温度上限要求 **78℃**。未触发温度停止。

所有记录的 requested / enforced power limit 均为 **150W**；瞬时 power draw 峰值 **154.659W**。这是完整采样中的实际值，文档没有将 150W 设定值当作瞬时功率的绝对上限。

测试结束后，第一次 GPU 状态采样核心为 **32℃**、功耗 **28.76W**；检查未发现 `gpu_burn` 残留进程。

## 这次没有验证的内容

没有做长时间老化、多次冷启动统计、全部地址显存专测、多卡并发、ECC、额外 4 SM、其他功率上限、其他主板或 BAR1 大小性能对照。上游作者的双卡 8GB 结果单独归属作者，不计入本机实验次数。

host/guest Secure Boot EFI 状态和 BIOS 菜单中的具体开关未单独读取；本次验证的是实际加载模块、IOMMU/VFIO 工作、4G 以上资源分配和运行结果。原有 512GiB PCI hole / 256GiB OVMF MMIO 参数被保留，没有测量最小值。

## 附件处理

本次数据的数值、时间戳、PCI 地址及构建哈希被保留。GPU UUID 统一替换为 `GPU-REDACTED`，hostname 替换为通用标签，日志统一换行；boot ID、SSH 凭据、私有地址和原工作目录不作为发布附件。公开的内核附件是成功路径的日志摘录，错误筛查结果另有 JSON，不能把摘录本身当作完整系统日志。

运行 `python3 tools/verify_evidence.py` 会离线检查日志最终 OK、全部报告的错误数、采样条数、温度峰值、150W 设定、显存占用、host 核验项以及仓库内链接。该检查不访问 GPU，不会重新启动负载。
