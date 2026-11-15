import sys, zipfile
src, dst = sys.argv[1], sys.argv[2]
SLUGS = ['oedipuscoloneus', 'trachiniae', 'oedipustyrannus']
with zipfile.ZipFile(src) as zi, zipfile.ZipFile(dst, 'w') as zo:
    for info in zi.infolist():
        if info.filename.startswith('META-INF/') and info.filename.upper().endswith(('.SF', '.RSA', '.DSA', '.EC', 'MANIFEST.MF')):
            continue
        data = zi.read(info.filename)
        if info.filename == 'base/assets/data/catalog.json':
            s = data.decode()
            for slug in SLUGS:
                key = '"slug": "%s",' % slug
                n = s.count(key)
                assert n == 1, (slug, n)
                s = s.replace(key, key + '\n  "google_play": "yes",')
            data = s.encode()
        zo.writestr(info, data, compress_type=info.compress_type)
print('ok')
