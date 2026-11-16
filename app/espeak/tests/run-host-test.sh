#!/bin/sh
# Builds eSpeak NG from the checkout (app/espeak/espeak-ng, made by fetch-espeak.sh with the
# patches) for this computer with AddressSanitizer, the same sources and config.h as the app's
# native build, and runs phoneme_input_test.c against the app's compiled data
# (src/main/assets/espeak-ng-data). Needs clang (or gcc) only; writes to a temporary folder.
# Fails if the test fails, AddressSanitizer reports an error, or eSpeak tries to load a
# dictionary the app does not ship (the English fallback that crashed the app).
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
ESPEAK="$HERE/../espeak-ng"
CPP="$HERE/../src/main/cpp"
ASSETS="$HERE/../src/main/assets/espeak-ng-data"
CC=${CC:-clang}
[ -f "$ESPEAK/src/libespeak-ng/speech.c" ] || { echo "run app/espeak/fetch-espeak.sh first"; exit 2; }
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
FLAGS="-g -O1 -fsanitize=address -fno-omit-frame-pointer -fwrapv -w"
INC="-I$CPP/config -I$ESPEAK/src/include -I$ESPEAK/src/include/compat -I$ESPEAK/src/ucd-tools/src/include"
for f in common mnemonics error ieee80 compiledata compiledict dictionary encoding intonation \
         langopts numbers phoneme phonemelist readclause setlengths soundicon spect ssml synthdata \
         synthesize tr_languages translate translateword voices wavegen speech espeak_api klatt; do
    $CC -c $FLAGS $INC -DLIBESPEAK_NG_EXPORT=1 -DPATH_ESPEAK_DATA='"/nonexistent"' "$ESPEAK/src/libespeak-ng/$f.c" -o "$WORK/$f.o"
done
for f in case categories ctype proplist scripts tostring; do
    $CC -c $FLAGS -I"$ESPEAK/src/ucd-tools/src/include" "$ESPEAK/src/ucd-tools/src/$f.c" -o "$WORK/ucd_$f.o"
done
$CC $FLAGS -I"$ESPEAK/src/include" "$HERE/phoneme_input_test.c" "$WORK"/*.o -lm -o "$WORK/test"
mkdir -p "$WORK/data"
cp -r "$ASSETS" "$WORK/data/espeak-ng-data"
status=0
"$WORK/test" "$WORK/data" 2> "$WORK/stderr" || status=$?
if grep -q "dictionary file" "$WORK/stderr"; then
    echo "FAIL eSpeak fell back on a dictionary the app does not ship:"; status=1
fi
cat "$WORK/stderr"
exit $status
