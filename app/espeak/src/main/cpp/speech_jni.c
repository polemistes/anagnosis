/*
 * The reader's voice: a thin JNI layer over eSpeak NG's synchronous API. Speech is synthesised
 * into memory, one utterance (a sentence of the text, as eSpeak phonemes in [[ ]]) at a time; the
 * app plays the samples itself. Word events give, for every word, its place in the input and the
 * sample at which it starts, so that the reader can highlight the word being spoken.
 *
 * eSpeak is not re-entrant: the Kotlin side (ESpeak) calls these under one lock.
 */
#include <jni.h>
#include <stdlib.h>
#include <string.h>
#include <espeak-ng/speak_lib.h>

static short *samples = NULL;
static int n_samples = 0, cap_samples = 0;
static int *events = NULL;        /* pairs: character offset in the input, sample */
static int n_events = 0, cap_events = 0;
static volatile int aborting = 0;

static int callback(short *wav, int n, espeak_EVENT *ev) {
    if (wav != NULL && n > 0) {
        if (n_samples + n > cap_samples) {
            int cap = cap_samples ? cap_samples : 1 << 16;
            while (cap < n_samples + n) cap *= 2;
            short *grown = realloc(samples, cap * sizeof(short));
            if (grown == NULL) return 1;
            samples = grown;
            cap_samples = cap;
        }
        memcpy(samples + n_samples, wav, n * sizeof(short));
        n_samples += n;
    }
    for (; ev != NULL && ev->type != espeakEVENT_LIST_TERMINATED; ev++) {
        if (ev->type != espeakEVENT_WORD) continue;
        if (n_events + 2 > cap_events) {
            int cap = cap_events ? cap_events * 2 : 256;
            int *grown = realloc(events, cap * sizeof(int));
            if (grown == NULL) return 1;
            events = grown;
            cap_events = cap;
        }
        events[n_events++] = ev->text_position - 1;  /* eSpeak counts from 1 */
        events[n_events++] = ev->sample;
    }
    return aborting ? 1 : 0;
}

JNIEXPORT jint JNICALL
Java_no_anagnosis_espeak_ESpeakNative_init(JNIEnv *env, jclass cls, jstring path) {
    const char *p = (*env)->GetStringUTFChars(env, path, NULL);
    int rate = espeak_Initialize(AUDIO_OUTPUT_SYNCHRONOUS, 0, p, espeakINITIALIZE_DONT_EXIT);
    (*env)->ReleaseStringUTFChars(env, path, p);
    if (rate > 0) espeak_SetSynthCallback(callback);
    return rate;
}

JNIEXPORT jboolean JNICALL
Java_no_anagnosis_espeak_ESpeakNative_setVoice(JNIEnv *env, jclass cls, jstring name) {
    const char *n = (*env)->GetStringUTFChars(env, name, NULL);
    espeak_ERROR err = espeak_SetVoiceByName(n);
    (*env)->ReleaseStringUTFChars(env, name, n);
    return err == EE_OK ? JNI_TRUE : JNI_FALSE;
}

JNIEXPORT jshortArray JNICALL
Java_no_anagnosis_espeak_ESpeakNative_synth(JNIEnv *env, jclass cls, jstring text, jint wpm) {
    const char *t = (*env)->GetStringUTFChars(env, text, NULL);
    n_samples = 0;
    n_events = 0;
    aborting = 0;
    espeak_SetParameter(espeakRATE, wpm, 0);
    espeak_Synth(t, strlen(t) + 1, 0, POS_CHARACTER, 0, espeakCHARS_UTF8 | espeakPHONEMES, NULL, NULL);
    espeak_Synchronize();
    (*env)->ReleaseStringUTFChars(env, text, t);
    jshortArray out = (*env)->NewShortArray(env, n_samples);
    if (out != NULL && n_samples > 0) (*env)->SetShortArrayRegion(env, out, 0, n_samples, samples);
    return out;
}

JNIEXPORT jintArray JNICALL
Java_no_anagnosis_espeak_ESpeakNative_wordEvents(JNIEnv *env, jclass cls) {
    jintArray out = (*env)->NewIntArray(env, n_events);
    if (out != NULL && n_events > 0) (*env)->SetIntArrayRegion(env, out, 0, n_events, events);
    return out;
}

JNIEXPORT void JNICALL
Java_no_anagnosis_espeak_ESpeakNative_abort(JNIEnv *env, jclass cls) {
    aborting = 1;
}
