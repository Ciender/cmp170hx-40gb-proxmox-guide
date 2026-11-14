# 原版 watcher 来源

- Repository: https://github.com/Johnnydaboy/cmpunlocker
- Branch: `homelab-dual-cmp170hx`
- Commit: `658110d5d1f15f7174d18f57caad4cab7d04593a`
- Original path: `tools/cmp-gen2-watch.c`
- SHA256: `d39d2b76dfac1b63c8af9efe7857055c3f5d1873184f8b3eea1aaa7d0304710e`
- License: `GPL-2.0-only`；同目录 LICENSE 来自该仓库。

文件保持逐字节一致。原文件注明基于 cmpunlocker PR #35，并说明本分支达到目标后退役单卡的处理。

本次成功部署只编译这个 C 文件并安装启动 unit，没有运行文件注释提及的完整 watch-setup/initramfs 安装流程。PVE 中的 initramfs 修改用于早期 VFIO 绑定；watcher 自身由 systemd 在 pve-guests 之前启动。
