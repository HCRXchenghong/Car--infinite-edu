"""Archive the hardware documentation package only, with a SHA256 manifest."""
from pathlib import Path
import csv
import hashlib
import zipfile

ROOT=Path(__file__).resolve().parents[1]
manifest=ROOT/'打印版/交付文件SHA256.csv'
files=sorted(p for p in ROOT.rglob('*') if p.is_file() and p!=manifest and '__pycache__' not in p.parts and p.name!='.DS_Store')
assert all(not p.is_symlink() for p in files)
with manifest.open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f); w.writerow(['文件','字节数','SHA256'])
    for p in files: w.writerow([str(p.relative_to(ROOT)),p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest()])
dest=ROOT.parent/'硬件实施资料包_HW-R1.zip'
with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in files+[manifest]: z.write(p,arcname=str(p.relative_to(ROOT.parent)))
with zipfile.ZipFile(dest) as z:
    assert z.testzip() is None
    assert len(z.namelist())==len(files)+1
    for p in files+[manifest]:
        assert hashlib.sha256(z.read(str(p.relative_to(ROOT.parent)))).digest()==hashlib.sha256(p.read_bytes()).digest(),p
print('Archive:',dest)
print('Files:',len(files)+1)
print('SHA256:',hashlib.sha256(dest.read_bytes()).hexdigest())
