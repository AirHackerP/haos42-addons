#!/usr/bin/env python3
"""
Patches rpihw.c to force Pi 4 detection in Docker containers.
Bypasses /proc/device-tree access issues.
"""
import re
import sys

def patch_rpihw(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Find and replace the rpi_hw_detect function
    pattern = r'(const rpi_hw_t \*rpi_hw_detect\(void\)\s*\{)\s*(const rpi_hw_t \*result = NULL;\s*uint32_t rev;\s*unsigned i;)'

    replacement = r'''\1
    /* Docker container workaround: Force Pi 4 detection
     * Container cannot access /proc/device-tree for hardware detection
     * Search for any Pi 4 entry (hwver & 0xFF0 == 0x3110) and return it
     */
    unsigned i;
    for (i = 0; i < (sizeof(rpi_hw_info) / sizeof(rpi_hw_info[0])); i++) {
        if ((rpi_hw_info[i].hwver & 0x00FF0) == 0x03110) return &rpi_hw_info[i];
    }
    const rpi_hw_t *result = NULL;
    uint32_t rev;'''

    modified = re.sub(pattern, replacement, content, count=1, flags=re.MULTILINE | re.DOTALL)

    if modified == content:
        print("ERROR: Pattern not found in rpihw.c", file=sys.stderr)
        sys.exit(1)

    with open(filepath, 'w') as f:
        f.write(modified)

    print(f"Successfully patched {filepath}")

if __name__ == '__main__':
    patch_rpihw('rpihw.c')
