# 仓库获取、检查与维护

公开仓库：[Ciender/cmp170hx-40gb-proxmox-guide](https://github.com/Ciender/cmp170hx-40gb-proxmox-guide)。默认分支为 `main`。

## 1. 获取文档和配置

```bash
git clone https://github.com/Ciender/cmp170hx-40gb-proxmox-guide.git
cd cmp170hx-40gb-proxmox-guide
```

也可在 GitHub 网页选择 Code → Download ZIP。网页会直接显示根目录 README；曲线、源码说明、配置模板和脱敏证据使用仓库内相对路径。

## 2. 离线核验

```bash
python3 tools/verify_evidence.py
python3 -m compileall -q scripts tools
cc -O2 -Wall -Wextra -o /tmp/cmp-gen2-watch third_party/cmp-gen2-watch/cmp-gen2-watch.c
```

以上检查不启动 GPU 负载，也不运行 watcher。文档中有实际硬件操作的命令已分别标注 PVE / guest，复现前须按本机拓扑修改案例地址。

仓库不包含驱动安装包、已编译内核模块或完整系统备份。NVIDIA 驱动源码及 gpu-burn 由 README 中的固定上游版本获取。

## 3. 维护者更新

使用有仓库写权限的 GitHub 账号登录后，先核对证据，再提交：

```bash
python3 tools/verify_evidence.py
git diff --check
git add .
git commit -m "Update the CMP 170HX reproduction guide"
git push origin main
```

本次成功数据保存在 `evidence/2026-11-14/`，并带有 SHA256 清单。后续硬件实验应另建日期目录并明确测试条件，保留已有原始数据；仅修改文字说明不需要重跑 GPU 压测。

`.github/workflows/validate.yml` 在 push 和 pull request 时执行离线证据检查、Python 语法检查和 watcher 编译，不需要 GPU runner。

## 4. 来源和许可证

根目录 MIT 许可证用于原创文档与辅助脚本；原 watcher 保留 GPLv2，第三方 unit 保留 Apache-2.0 来源说明，见 [NOTICE](../NOTICE.md)。原作者的驱动修复及本次环境适配分别在 [源码说明](SOURCE-ANALYSIS.zh-CN.md)中列明。
