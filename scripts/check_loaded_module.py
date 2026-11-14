#!/usr/bin/env python3
"""Compare the loaded NVIDIA image with the installed image by GNU build ID.

srcversion alone cannot distinguish all NVIDIA RM-source patch changes.
This command reads metadata only and never opens a GPU device.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess

module = Path('/lib/modules') / os.uname().release / 'updates/cmpunlocker/nvidia.ko'
note = Path('/sys/module/nvidia/notes/.note.gnu.build-id').read_bytes()
namesz, descsz, note_type = struct.unpack_from('<III', note)
assert note_type == 3 and note[12:12 + namesz].rstrip(b'\0') == b'GNU'
offset = 12 + (namesz + 3) // 4 * 4
loaded = note[offset:offset + descsz].hex()
notes = subprocess.check_output(['readelf', '-n', str(module)], text=True)
match = re.search(r'Build ID:\s*([0-9a-f]+)', notes)
assert match is not None, 'Installed module has no GNU build ID'
installed = match.group(1)
result = {
    'loaded_build_id': loaded,
    'installed_build_id': installed,
    'match': loaded == installed,
    'installed_path': str(module),
    'installed_sha256': hashlib.sha256(module.read_bytes()).hexdigest(),
    'loaded_version': Path('/sys/module/nvidia/version').read_text().strip(),
    'loaded_srcversion': Path('/sys/module/nvidia/srcversion').read_text().strip(),
    'gpu_accessed': False,
}
print(json.dumps(result, indent=2))
raise SystemExit(0 if result['match'] else 1)
