# eSpeak NG (GPL-3.0-or-later) for the reader's voice, built from the checkout made by
# app/espeak/fetch-espeak.sh. Only the library is compiled (no command-line tool, no data: the
# data is compiled by the pipeline, see build-speech-data), with Klatt, speechPlayer, MBROLA,
# libsonic, audio output and the asynchronous API left out: the app synthesises into memory.
cmake_minimum_required(VERSION 3.22)
project(anagnosisspeech C)

set(ESPEAK ${CMAKE_CURRENT_SOURCE_DIR}/../../../espeak-ng)
if(NOT EXISTS ${ESPEAK}/src/libespeak-ng/speech.c)
  message(FATAL_ERROR "eSpeak NG sources are missing: run app/espeak/fetch-espeak.sh")
endif()

add_library(ucd STATIC
  ${ESPEAK}/src/ucd-tools/src/case.c
  ${ESPEAK}/src/ucd-tools/src/categories.c
  ${ESPEAK}/src/ucd-tools/src/ctype.c
  ${ESPEAK}/src/ucd-tools/src/proplist.c
  ${ESPEAK}/src/ucd-tools/src/scripts.c
  ${ESPEAK}/src/ucd-tools/src/tostring.c
)
set_property(TARGET ucd PROPERTY POSITION_INDEPENDENT_CODE ON)
target_include_directories(ucd PUBLIC ${ESPEAK}/src/ucd-tools/src/include)

set(LIB ${ESPEAK}/src/libespeak-ng)
add_library(espeak-ng STATIC
  ${LIB}/common.c ${LIB}/mnemonics.c ${LIB}/error.c ${LIB}/ieee80.c
  ${LIB}/compiledata.c ${LIB}/compiledict.c
  ${LIB}/dictionary.c ${LIB}/encoding.c ${LIB}/intonation.c ${LIB}/langopts.c ${LIB}/numbers.c
  ${LIB}/phoneme.c ${LIB}/phonemelist.c ${LIB}/readclause.c ${LIB}/setlengths.c ${LIB}/soundicon.c
  ${LIB}/spect.c ${LIB}/ssml.c ${LIB}/synthdata.c ${LIB}/synthesize.c ${LIB}/tr_languages.c
  ${LIB}/translate.c ${LIB}/translateword.c ${LIB}/voices.c ${LIB}/wavegen.c ${LIB}/speech.c
  ${LIB}/espeak_api.c
)
set_property(TARGET espeak-ng PROPERTY POSITION_INDEPENDENT_CODE ON)
# config.h as eSpeak's configure step writes it for these options
target_include_directories(espeak-ng PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/config ${ESPEAK}/src/include ${ESPEAK}/src/include/compat)
target_include_directories(espeak-ng PUBLIC ${ESPEAK}/src/include)
target_compile_definitions(espeak-ng PRIVATE LIBESPEAK_NG_EXPORT=1 "PATH_ESPEAK_DATA=\"/nonexistent\"")
target_compile_definitions(espeak-ng INTERFACE LIBESPEAK_NG_EXPORT=1)
target_compile_options(espeak-ng PRIVATE -fvisibility=hidden -fno-exceptions -fwrapv -Wno-unused-parameter)
target_link_libraries(espeak-ng PRIVATE ucd m)

add_library(anagnosisspeech SHARED speech_jni.c)
target_link_libraries(anagnosisspeech PRIVATE espeak-ng log)
