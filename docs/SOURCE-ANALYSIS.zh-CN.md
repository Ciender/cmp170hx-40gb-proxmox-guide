# 成功路线的源码修复与贡献归属

本文对照本地固定源码说明“为什么采用这套组合”，并把源码事实、作者的说明和本次实测分开。完整操作步骤在 [README](../README.md)。

## 1. 固定到哪个提交

本次使用 [Johnnydaboy/cmpunlocker 的 `658110d`](https://github.com/Johnnydaboy/cmpunlocker/tree/658110d5d1f15f7174d18f57caad4cab7d04593a)。其中两个直接相关的历史提交是：

| 提交 | 作者 / 来源 | 作用 |
| --- | --- | --- |
| [`209d4a48588087f4e0cf3087f974ff70593d8505`](https://github.com/Johnnydaboy/cmpunlocker/commit/209d4a48588087f4e0cf3087f974ff70593d8505) | Jonathan / Johnnydaboy | `Fix dual CMP 170HX unlock under Proxmox VFIO`：调整默认补丁集合、签名恢复、WPR2、GSP 初始化及相关 Gen2 写入 |
| [`658110d5d1f15f7174d18f57caad4cab7d04593a`](https://github.com/Johnnydaboy/cmpunlocker/commit/658110d5d1f15f7174d18f57caad4cab7d04593a) | Jonathan / Johnnydaboy | 补充可复现的双 CMP Proxmox 部署文档 |
| [`f51da030ef4260656288edf07e95ae45f339aea8`](https://github.com/Johnnydaboy/cmpunlocker/commit/f51da030ef4260656288edf07e95ae45f339aea8) | 原上游，Amogh Munikote 及共同贡献者 | 高端显存区继续保留，避免把 WPR2 所在区域交回普通分配器 |

`f51da03` 是这个分支包含的上游修复，不是本次现场编写，也不能全部归于 Johnny。

## 2. BAR1：显存容量与 PCI 窗口必须分开

代码入口：[driver/build.sh](https://github.com/Johnnydaboy/cmpunlocker/blob/658110d5d1f15f7174d18f57caad4cab7d04593a/driver/build.sh)。

该提交的默认补丁数组不含 `bar1-resize-unlock.patch`，只有显式设置 `CMPUNLOCKER_ENABLE_BAR1_RESIZE=1` 才追加它。本次值是 `0`。

这里要处理的是两层状态的一致性：GPU 的物理 BAR1 大小由硬件状态决定；PVE/QEMU 给 guest 建立的 PCI 窗口和 VFIO 映射又是另一层。如果 VM 已启动后，guest 驱动通过 GPU 寄存器改变物理 BAR，而 QEMU 仍按原始大小组织映射，二者就可能分歧。专用文档把这与 BAR2/MMU 初始化故障联系起来。

本次成功启动的实测状态为：

| 层次 | BAR1 |
| --- | --- |
| GPU Physical Resizable BAR | current size 64MiB |
| PVE GPU resource 1 | `0xd2ff8000000–0xd2ffbffffff`，64MiB |
| GPU 配置空间 BAR1 基址 | 与 PVE resource 1 一致 |
| guest resource 1 | `0x380800000000–0x380803ffffff`，64MiB |
| NVML 显存 | 40960MiB |
| gpu-burn 分配并参与计算 | 36161MiB |

host 和 guest 的基址不相同是两个地址空间的正常表示；本次核验的是每一层所对应的物理状态和映射大小，不要求它们的基址数值相等。

实际结论是：**本次 40GB 显存解锁和大于原始 10GB 容量的计算负载可以在 64MiB BAR1 下工作。** 没有在这台机器上测量不同 BAR1 大小的性能，也不由此推广到所有驱动和平台。

## 3. 签名缓冲：分配大小不能当作签名长度

代码入口：[sec2-postbl-plm-ss-cfg.patch](https://github.com/Johnnydaboy/cmpunlocker/blob/658110d5d1f15f7174d18f57caad4cab7d04593a/driver/patches/sec2-postbl-plm-ss-cfg.patch)。

补丁使用原厂签名保存区 `pStockSignatureData` / `stockSignatureSize`，并为利用过程保留较大的签名内存描述符。这里有两个不同量：

| 量 | 本次值 / 用途 |
| --- | --- |
| 原厂 GSP 签名真实长度 | 4096 bytes |
| 利用阶段缓冲分配大小 | `0xf800`，约 62KiB |

Johnny 的修复没有在恢复原厂签名时销毁并重建一个只有 4096 字节的小描述符，而是在现有描述符中清零、复制原始签名并刷新缓存。随后重新填充 WPR 元数据时，明确执行相当于 `sizeOfSignature = stockSignatureSize` 的恢复，避免把整个利用缓冲的分配大小解释成有效签名长度。

作者文档说明错误的长度会造成 Booter `0xb`。本次成功日志直接证实：

```text
saved stock signature (4096 bytes)
WPR meta updated fbSize=0x0000000a00000000 ... sigSize=4096
```

这是对当前成功路径的验证，没有做额外的故障注入，也不把该修复扩展表述为对所有异常重试路径的形式化安全证明。

## 4. WPR2：硬件边界恢复与分配器保留是两件事

在 SEC2 写入之前，补丁保存 WPR2 寄存器；写入并更新显存几何后，再把保存值写回 `0x001fa824`、`0x001fa828`。相关 WPR 元数据描述符会刷新缓存。

本次日志中保存和恢复的值为：

```text
WPR2 lo=0x1ffffe00 hi=0x00000000
```

这两个值用于证明代码恢复了此前保存的硬件状态；不能仅凭这行就把它解释成最终 40GB WPR 区间。后续元数据给出的区间是：

```text
fbSize   = 0x0000000a00000000
wprStart = 0x00000009f7600000
wprEnd   = 0x00000009fff00000
```

此外，[late-pma.patch](https://github.com/Johnnydaboy/cmpunlocker/blob/658110d5d1f15f7174d18f57caad4cab7d04593a/driver/patches/late-pma.patch)延续上游 `f51da03` 的处理：保留区域遍历和日志，但不把高端保留区重新注册进 PMA。

本次输出：

```text
candidate=6 base=0x9f7500000 limit=0x9ffffffff left reserved (backs WPR2)
```

这段约 139MiB 的区域与 WPR2 相关空间相交。保留它会占用一部分可分配容量，但可以避免普通 CUDA 分配覆盖正在使用的固件空间。不能为了让容量数字更接近 NVML 总数而把这段区域强行交回分配器。

## 5. 初始化顺序：保留已有锁，删去不需要的路径

补丁在 `_kgspShouldRelaxGspInitLocking` 中对两种目标 CMP ID 返回 `NV_FALSE`，让初始化继续受已有锁约束。作者是在双卡 Q35/VFIO 环境处理并行 GSP 初始化时序问题；本次只有单卡，没有单独验证双卡竞争条件。

`driver/build.sh` 的默认补丁集合排除：

- `booter-verify.patch`；
- `pcie-gen2-probe-retrain.patch`；
- `bar1-resize-unlock.patch`，除非明确 opt-in。

本次按默认集合安装，没有为了复制通用 README 的功能列表而把这些补丁重新加入。

## 6. Gen2：guest 准备端点，host 操作物理父端口

代码入口：[pcie-gen2.patch](https://github.com/Johnnydaboy/cmpunlocker/blob/658110d5d1f15f7174d18f57caad4cab7d04593a/driver/patches/pcie-gen2.patch)、[cmp-gen2-watch.c](https://github.com/Johnnydaboy/cmpunlocker/blob/658110d5d1f15f7174d18f57caad4cab7d04593a/tools/cmp-gen2-watch.c)。

### 移除不属于 Gen2 的 ECC PLM 写入

`209d4a4` 从 Gen2 的寄存器表删除了：

```text
address: 0x00823800
label:   FEAT_OVR_ECC_PLM
```

作者专用文档指出，在其第二张 GPU 上，该写入是从预期 `0x31` 转为致命 `0x15` 的精确位置。这里说明的是作者的定位结果。本次使用移除该写入的源码，初始化和后续计算测试成功；没有再次启用该写入进行对照压测。

### 在窗口内重训真实物理链路

watcher 原文件说明：某些组合中，端点公布 Gen2 的窗口约 430ms。这个窗口长度是作者在源码中记录的观察值；本机只验证了窗口被捕捉并训练成功，没有单独测定其持续长度。

watcher 做的工作是：

1. 枚举受支持的 `10de:20c2 / 2082`。
2. 从 sysfs 拓扑向上寻找可重训的真实 root/downstream port。
3. 以 1ms 周期读取端点 LnkCap。
4. 检测到目标能力后，设置父端口 Target Link Speed，写 Retrain Link。
5. 根据 link status 判断是否已达到目标；成功后把该卡从后续重训中退役。

源码注明 watcher 基于 cmpunlocker PR #35，并在此分支加入达到目标后退役的行为。本仓库提供的是该分支原文件，SHA256 与本次 PVE 编译源相同。

本次拓扑为 `51:00.0 → 50:02.0`，实际日志是：

```text
T+43.135 ... LnkCap 00456101 -> 00456102
T+43.135 ... retrain via 0000:50:02.0
T+43.136 ... trained at Gen2; retiring watcher for this card
```

上述 `T+` 是 watcher 自己的相对计时，不应写成精确的系统上电秒数。guest 与 PVE 两端最终都读到 Gen2 ×4。

## 7. 本次本地适配与上游解锁代码的边界

| 部分 | 本次处理 |
| --- | --- |
| 七份驱动补丁 | 使用固定分支原文件；没有插入本地驱动代码 |
| NVIDIA 基础源码 | tag `610.43.02`，归档 SHA256 已核验 |
| 10GB 配置 | profile=10gb，单卡 inventory，目标 40960MiB；运行时按 2082 选择几何 |
| Debian headers | 通过 make 变量指定 source/build 分离目录 |
| 安装时机 | `CMPUNLOCKER_SKIP_RELOAD=1`，等待冷启动 |
| host watcher | 使用作者原 C 源码 |
| host unit | 基于作者配套 unit，增加本机单卡拓扑前置检查 |
| host VFIO | 新增 2082 早期绑定、disable_idle_d3=1，保留其他设备配置 |
| VM | 设置 onboot，使其在 watcher 窗口内启动；保留原有 MMIO 参数 |
| 功率服务 | 使用单卡 UUID 定位的 150W helper，不使用作者双卡 180W 示例 |
| 压测 | 固定 gpu-burn 版本，增加核心温度采样和提前停止保护 |

因此，本文的成果是**把作者提供的 VFIO 路线适配到本机 2082 单卡，并完成启动、物理链路、CUDA 属性和短时负载验收**。不宣称重新实现了解锁算法，也不宣称对所有 170HX、BIOS 或虚拟化平台完成兼容性验证。
