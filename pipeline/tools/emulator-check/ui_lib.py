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
