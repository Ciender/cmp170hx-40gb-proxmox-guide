#!/usr/bin/python3
from pathlib import Path
sys=Path('/sys/bus/pci/devices')
gpus=[p for p in sys.iterdir() if (p/'vendor').read_text().strip()=='0x10de' and (p/'device').read_text().strip() in ['0x20c2','0x2082']]
assert len(gpus)==1 and gpus[0].name=='0000:51:00.0', 'Unexpected CMP topology; no retraining permitted'
gpu=gpus[0]
assert (gpu/'device').read_text().strip()=='0x2082', 'Unexpected card'
assert gpu.resolve().parent.name=='0000:50:02.0', 'Unexpected physical parent'
assert (gpu/'driver').resolve().name=='vfio-pci', 'Card is not bound to VFIO'
print('Verified single 2082: 51:00.0 -> physical parent 50:02.0, vfio-pci')
