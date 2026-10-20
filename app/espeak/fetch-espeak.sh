#!/bin/sh
# Fetches eSpeak NG (GPL-3.0-or-later) at the release the app is built against into
# app/espeak/espeak-ng/ (ignored by git) and applies the patches in app/espeak/patches/.
# Run from anywhere; run again after a patch changes (it starts from a clean checkout).
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
TAG=1.52.0
rm -rf "$HERE/espeak-ng"
git clone --depth 1 --branch "$TAG" https://github.com/espeak-ng/espeak-ng.git "$HERE/espeak-ng"
for p in "$HERE"/patches/*.patch; do
    [ -e "$p" ] || continue
    echo "applying $(basename "$p")"
    git -C "$HERE/espeak-ng" apply "$p"
done
