# Tesseract models for the OCR of scans

The `.traineddata` files in this folder are Tesseract's `tessdata_best` models
(https://github.com/tesseract-ocr/tessdata_best, Apache License 2.0): the float LSTM
models, which read better than the `tessdata` models the Arch packages install in
`/usr/share/tessdata`, and are the ones that can be fine-tuned. They are not kept in
git (`.gitignore`); they were copied on 2026-10-19 from the Glaukopis project's
language packaging (`packaging/build/languages/tessdata_best`, itself fetched from
the repository above), and can be fetched again from the same repository:

    curl -L -o grc.traineddata https://raw.githubusercontent.com/tesseract-ocr/tessdata_best/main/grc.traineddata

| file | language | size |
|---|---|---|
| `grc.traineddata` | ancient (polytonic) Greek | 5.2 MB |
| `eng.traineddata` | English | 15.4 MB |
| `lat.traineddata` | Latin | 9.7 MB |

Use them with `--tessdata-dir pipeline/tessdata`, for example

    tesseract page.png out --tessdata-dir pipeline/tessdata -l grc+eng+lat --psm 4 hocr tsv

Checked 2026-10-19: `tesseract --list-langs --tessdata-dir pipeline/tessdata` lists eng, grc, lat
(Tesseract 5.5.3).
