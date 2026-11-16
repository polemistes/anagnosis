/*
 * Host test for eSpeak NG as the reader uses it (app/espeak/src/main/cpp/speech_jni.c): the
 * same calls, with the app's compiled data, on inputs that crashed the app (2026-11-17,
 * SIGSEGV in LookupDict2 from LookupLetter). Run by run-host-test.sh, which builds the library
 * from the checkout with AddressSanitizer.
 *
 * The crash: eSpeak's ReadClause lost track of [[phonemes]] in two cases, cut the clause inside
 * the brackets and read the rest ("]]", "_:" ...) as text; naming such a character sends eSpeak
 * to its English dictionary, which the app does not ship, and the half-made English translator
 * was read through uninitialised pointers. The cases:
 *   1. an elided word joined to the next ("[[a0d]][[o0 _:]]") when the next carries a pause;
 *   2. an utterance over about 725 bytes (a long sentence).
 * The test fails (ASan report, or the English fallback on stderr, or a wrong result) without
 * patches/phoneme-input-clauses.patch and passes with it.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <espeak-ng/speak_lib.h>

static long n_samples, n_events;
static unsigned long long hash;
static int events[4096];

static int callback(short *wav, int n, espeak_EVENT *ev) {
    for (int i = 0; wav != NULL && i < n; i++) hash = (hash ^ (unsigned short)wav[i]) * 1099511628211ULL;
    if (wav != NULL && n > 0) n_samples += n;
    for (; ev != NULL && ev->type != espeakEVENT_LIST_TERMINATED; ev++)
        if (ev->type == espeakEVENT_WORD && n_events < 4096) events[n_events++] = ev->text_position - 1;
    return 0;
}

static const char *current_voice = "";

static void synth(const char *voice, const char *text) {
    if (strcmp(voice, current_voice) != 0) {
        if (espeak_SetVoiceByName(voice) != EE_OK) { printf("FAIL no voice %s\n", voice); exit(1); }
        current_voice = voice;
    }
    n_samples = n_events = 0;
    hash = 1469598103934665603ULL;
    espeak_SetParameter(espeakRATE, 100, 0);
    espeak_SetParameter(espeakPITCH, 50, 0);
    espeak_Synth(text, strlen(text) + 1, 0, POS_CHARACTER, 0, espeakCHARS_UTF8 | espeakPHONEMES, NULL, NULL);
    espeak_Synchronize();
}

static int failures = 0;

/* Whether every word of [text] (each "[[") got its word event, at the word's first phoneme
 * (past a stress mark that begins the word: eSpeak reports a Koine "[['kE]]" there). */
static int all_words_have_events(const char *text) {
    int e = 0;
    for (const char *p = strstr(text, "[["); p != NULL; p = strstr(p + 2, "[[")) {
        int want = (int)(p - text) + 2 + (p[2] == '\'' || p[2] == '%');
        while (e < n_events && events[e] != want) e++;
        if (e == n_events) return 0;
    }
    return 1;
}

/*
 * A word joined to the one before ("]][[", an elided word) must be read as phonemes like any
 * other: every word gets its event, and the speech is as long as with a space between (eSpeak
 * ends a word at "]]" either way; the lengths differ by a few samples from one synthesis to the
 * next, so 1 % is allowed; the text read as text made it far longer).
 */
static void same_as_spaced(const char *voice, const char *joined) {
    char spaced[4096];
    const char *p = strstr(joined, "]][[");
    snprintf(spaced, sizeof spaced, "%.*s]] [[%s", (int)(p - joined), joined, p + 4);
    synth(voice, spaced);
    long n0 = n_samples;
    synth(voice, joined);
    int ok = n_samples > 0 && labs(n_samples - n0) * 100 <= n0 && all_words_have_events(joined);
    printf("%s joined word: %s (%ld samples, spaced %ld)\n", ok ? "ok  " : "FAIL", joined, n_samples, n0);
    failures += !ok;
}

/* A long utterance: spoken to its end (at least half as long as its words one by one; Koine
 * shortens unstressed repeats), every word with its event. */
static void long_utterance(const char *voice, const char *word, int count) {
    size_t wl = strlen(word);
    char *text = malloc(count * (wl + 1) + 1), *q = text;
    for (int i = 0; i < count; i++) { memcpy(q, word, wl); q += wl; *q++ = ' '; }
    q[-1] = 0;
    synth(voice, word);
    long one = n_samples;
    synth(voice, text);
    int ok = all_words_have_events(text) && n_samples > one * count / 2;
    printf("%s long utterance: %zu bytes, %ld samples (one word %ld)\n", ok ? "ok  " : "FAIL", strlen(text), n_samples, one);
    failures += !ok;
    free(text);
}

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "usage: %s DIR (holding espeak-ng-data)\n", argv[0]); return 2; }
    int rate = espeak_Initialize(AUDIO_OUTPUT_SYNCHRONOUS, 0, argv[1], espeakINITIALIZE_DONT_EXIT);
    if (rate <= 0) { printf("FAIL eSpeak did not start (%d)\n", rate); return 1; }
    espeak_SetSynthCallback(callback);

    same_as_spaced("grc", "[[a0d]][[o0 _:]]");
    same_as_spaced("grc", "[[a0d]][[o0 _::]]");
    /* Philoctetes 2, which crashed the app: Λήμνου, βροτοῖς ἄστιπτος οὐδʼ οἰκουμένη· */
    same_as_spaced("grc", "[[lE:2mnu:0 _:]] [[bro0toI3s]] [[a1sti0pto0s]] [[u:0d]][[oI0ku:0me1nE:0 _::]]");
    /* Philoctetes 9, ἀλλʼ ἀγρίαις at the end of the verse */
    same_as_spaced("grc", "[[pa0rE:3n]] [[he0kE:2loI0s]] [[pro0stHi0ge:3n _:]] [[a0ll]][[a0gri1aI0s _:]]");
    /* Koine (Matthew 2.3, μετʼ αὐτοῦ,) */
    same_as_spaced("grc-koine", "[[m%Et]][[af'tu _:]] [['kE]]");

    long_utterance("grc", "[[ka0ko1s]]", 61);
    long_utterance("grc", "[[ka0kO:3s _:]]", 200);
    long_utterance("grc-koine", "[[ka'kos]]", 120);

    printf(failures ? "%d FAILED\n" : "all passed\n", failures);
    return failures ? 1 : 0;
}
