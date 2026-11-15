#!/usr/bin/env python3
# goto.py VERSE TOTAL  -- drag the scrubber, then page until the verse is on the page
import sys, subprocess, re, time
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
ADB = '/home/proteus/Android/Sdk/platform-tools/adb'
import importlib.util
spec = importlib.util.spec_from_file_location('ui', __import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/ui_lib.py')
ui = importlib.util.module_from_spec(spec); spec.loader.exec_module(ui)
v = int(sys.argv[1]); total = int(sys.argv[2])
def rng():
    for t,b in ui.dump():
        m = re.match(r'Lines? (\d+)\D*?(?:–(\d+))?', t)
        if m and b[1] > 2000:
            a = int(m.group(1)); z = int(m.group(2) or a); return a, z
    return None
r = rng()
if not r: print('no range'); sys.exit(1)
if not (r[0] <= v <= r[1]) and abs(v - r[0]) > 60:
    x0, x1 = 50, 1030
    # find the dot: assume at current fraction
    cur = x0 + (x1-x0) * r[0] / total
    tgt = x0 + (x1-x0) * max(0, v - 10) / total
    subprocess.run([ADB,'shell','input','swipe',str(int(cur)),'2277',str(int(tgt)),'2277','1500'])
    time.sleep(1.5)
for _ in range(40):
    r = rng()
    if r is None: print('no range'); sys.exit(1)
    if r[0] <= v <= r[1]: break
    if v > r[1]: subprocess.run([ADB,'shell','input','swipe','900','1300','150','1300','200'])
    else: subprocess.run([ADB,'shell','input','swipe','150','1300','900','1300','200'])
    time.sleep(1.0)
print('range', r)
