[![English](../../assets/lang-en-active.svg)](ORIGIN.md) [![简体中文](../../assets/lang-zh.svg)](ORIGIN.zh-CN.md)

# Original watcher source

- Repository: https://github.com/Johnnydaboy/cmpunlocker
- Branch: `homelab-dual-cmp170hx`
- Commit: `658110d5d1f15f7174d18f57caad4cab7d04593a`
- Original path: `tools/cmp-gen2-watch.c`
- SHA256: `d39d2b76dfac1b63c8af9efe7857055c3f5d1873184f8b3eea1aaa7d0304710e`
- License: `GPL-2.0-only`; LICENSE in this directory is from that repository.

The source file is byte-for-byte unchanged. It credits cmpunlocker PR #35 and describes this branch's behavior of retiring each card after reaching the requested generation.

This deployment compiled this C file and installed its startup unit. It did not run the full watch-setup/initramfs installation mentioned in the source comments. The PVE initramfs changes provided early VFIO binding; the watcher itself started through systemd before pve-guests.
