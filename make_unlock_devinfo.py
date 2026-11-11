#!/usr/bin/env python3
# 从一份原始 devinfo dump 生成解锁镜像：把偏移 16 的 is_unlocked 置 1
# 用法: python3 make_unlock_devinfo.py <输入devinfo.bin> <输出.bin>
import sys, struct

MAGIC = b"ANDROID-BOOT!"

def main():
    if len(sys.argv) < 3:
        print("用法: python3 make_unlock_devinfo.py <输入devinfo.bin> <输出.bin>")
        sys.exit(1)
    inp, outp = sys.argv[1], sys.argv[2]
    d = bytearray(open(inp, "rb").read())
    if d[:len(MAGIC)] != MAGIC:
        print("错误: 不是 ANDROID-BOOT! 格式的 devinfo")
        sys.exit(1)
    if len(d) < 32:
        print("错误: 文件太小，不是合法 devinfo")
        sys.exit(1)
    struct.pack_into("<I", d, 16, 1)
    open(outp, "wb").write(d)
    print(f"已生成 {outp}: 偏移 16 (is_unlocked) = 1")

if __name__ == "__main__":
    main()
