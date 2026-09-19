"""Decode downloaded official ST API responses; never synthesize package pins."""
import base64
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
for src, name in [('/tmp/car_g474.json', 'STM32G474Q_B-C-E_Tx.xml'),
                  ('/tmp/car_g491.json', 'STM32G491V_C-E_Tx.xml')]:
    obj = json.loads(Path(src).read_text())
    data = base64.b64decode(obj['content'])
    out = ROOT / '资料' / name
    out.write_bytes(data)
    tree = ET.fromstring(data)
    print(name, 'blob', obj['sha'], tree.attrib)
    for item in tree:
        tag = item.tag.rsplit('}', 1)[-1]
        if tag == 'IP':
            print('IP', item.attrib)
        elif tag == 'Pin':
            signals = [x.attrib.get('Name') for x in item if x.tag.endswith('Signal')]
            print(item.attrib.get('Position'), item.attrib.get('Name'), ','.join(signals))
