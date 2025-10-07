import zipfile

with zipfile.ZipFile('base.zip', 'w') as zf:
    zf.writestr('file1.txt', 'version 1')
