#!/usr/bin/env python3
# ui.py dump | tap TEXT [n] | shot NAME [scale]
import sys, subprocess, re, xml.etree.ElementTree as ET
ADB = '/home/proteus/Android/Sdk/platform-tools/adb'
S = '/tmp/claude-1000/-home-proteus-koding-anagnosis/99bc5a94-1836-41e7-820b-bcdd1d76fe61/scratchpad/emulator-oc'
def dump():
    subprocess.run([ADB,'shell','uiautomator','dump','/sdcard/ui.xml'],capture_output=True)
    x = subprocess.run([ADB,'exec-out','cat','/sdcard/ui.xml'],capture_output=True).stdout.decode()
    root = ET.fromstring(x)
    out=[]
    for n in root.iter('node'):
        t = n.get('text') or n.get('content-desc') or ''
        if t.strip():
            b = list(map(int, re.findall(r'\d+', n.get('bounds'))))
            out.append((t, b))
    return out
cmd = sys.argv[1]
if cmd == 'dump':
    for t,b in dump(): print(b, t.replace('\n',' ⏎ ')[:200])
elif cmd == 'tap':
    want = sys.argv[2]; k = int(sys.argv[3]) if len(sys.argv)>3 else 0
    hits = [(t,b) for t,b in dump() if t == want] or [(t,b) for t,b in dump() if want in t]
    if not hits: print('NOT FOUND', want); sys.exit(1)
    t,b = hits[k]; x=(b[0]+b[2])//2; y=(b[1]+b[3])//2
    subprocess.run([ADB,'shell','input','tap',str(x),str(y)]); print('tapped', t[:60], x, y)
elif cmd == 'shot':
    name = sys.argv[2]; sc = float(sys.argv[3]) if len(sys.argv)>3 else 0.4
    png = subprocess.run([ADB,'exec-out','screencap','-p'],capture_output=True).stdout
    open(f'{S}/{name}.png','wb').write(png)
    from PIL import Image
    im = Image.open(f'{S}/{name}.png'); im.convert('RGB').resize((int(im.width*sc), int(im.height*sc))).save(f'{S}/small.jpg', quality=80)
    print('saved', name)
