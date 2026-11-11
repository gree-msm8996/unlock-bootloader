# Gree g0245d 解锁 bootloader 记录

## 背景
机器是 Gree g0245d，MSM8996（骁龙 820），出厂安卓 6.0。自己编译了内核 boot_g0245d.img，想用 `fastboot boot` 临时启动，一直报：

    Booting FAILED (remote: 'bootimage: incomplete or not signed')

TWRP 能 boot 起来，说明 bootloader 本身能加载镜像，只是对签名做了校验。

## 原理
bootloader 是 emmc_appsboot.mbn（aboot）。它在启动 boot/recovery 之前会读 devinfo 分区里的 `is_unlocked` 标志：

- `is_unlocked == 1`：打印 "Device is unlocked! Skipping verification"，跳过镜像签名校验，任何 boot.img 都能直接启动。
- `is_unlocked == 0`：走 keystore 证书链校验（镜像尾部那段双重签名），过不了就拒绝。

官方没给解锁工具，手上也没有能匹配 aboot 内嵌证书的私钥。aboot 里那张证书是 AOSP 早期 testkey（序列号 0x970f983909aa8949），公开源早轮换过，网上能下到的全是轮换后的，所以"自己给镜像签名"这条路走不通。剩下的就是直接改 devinfo 的 `is_unlocked`。

devinfo 分区格式（本机，魔数 ANDROID-BOOT!，小端 u32）：

    偏移 0    magic[16]            "ANDROID-BOOT!"
    偏移 16   is_unlocked          启动校验开关，置 1 即解锁
    偏移 20   is_tampered
    偏移 24   is_unlock_critical   出厂就是 1，和启动解锁无关
    偏移 28   charger_screen_enabled

本机的字段顺序和常见资料（CAF 标准把 is_unlocked 放在偏移 20）不一样，这里 is_unlocked 在偏移 16。这点卡了很久。

确认过程：把 emmc_appsboot.mbn 的 LOAD 段（文件偏移 0x8000，VMA 0x91600000）抠出来反汇编，定位 fastboot 命令表，找到 `oem device-info` 的 handler（入口 0x91633f74，ARM 模式）。里面 devinfo 的 RAM 基址是 0x916902e4，依次 `ldr r3,[r4,#0x10]` / `#0x14` / `#0x18` 对应 "Device unlocked" / "Device tampered" / "Device critical"，所以偏移 16 就是 is_unlocked。

## 操作步骤
前提：机器能进 fastboot，电脑装好 fastboot，且已 root（方便 dump devinfo 备份）。

1. 进 fastboot

       adb reboot bootloader

2. 备份当前 devinfo（建议先备份，9008 能恢复）

       dd if=/dev/block/platform/soc/624000.ufshc/by-name/devinfo of=/sdcard/devinfo_bak.bin
       adb pull /sdcard/devinfo_bak.bin

3. 刷入解锁镜像

       fastboot flash devinfo devinfo_unlocked.bin

4. 重启回 bootloader 确认

       fastboot reboot-bootloader
       fastboot oem device-info

   看到 `Device unlocked: true` 就说明生效了。

5. 启动第三方内核

       fastboot boot boot_g0245d.img

   不再报 "incomplete or not signed"。

要永久生效（不是每次 boot 临时进），把内核刷进 boot 分区：

       fastboot flash boot boot_g0245d.img

## 说明
- 只动 devinfo 一个分区，9008 完整包随时能恢复，不会变砖。
- devinfo_unlocked.bin 是当前这台机器 dump 出来、只把偏移 16 置 1 的结果。换同型号机器前最好自己先 dump 一份再改，避免其它字段不一致。
- 想锁回去：把备份的 devinfo 刷回去（偏移 16 改回 0）即可。

## 文件
- devinfo_unlocked.bin：解锁用的 devinfo 镜像
- make_unlock_devinfo.py：从一份原始 devinfo dump 生成解锁镜像（偏移 16 置 1）的脚本
