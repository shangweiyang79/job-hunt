#!/usr/bin/env bash
# Convert tailored .docx/.pptx to PDF with LibreOffice and print the page count.
#   bash scripts/render_pdf.sh out/2026-10-20_Acme/Resume.docx [more files...]
# Prints "<pages>\t<pdf path>" per file. Exits 2 if LibreOffice cannot be installed,
# in which case the routine ships the .docx/.pptx without a PDF.
# Page counts are approximate: the cloud has Noto Sans CJK, not 微軟正黑體.
set -u
if ! command -v soffice >/dev/null 2>&1; then
  (sudo -n true 2>/dev/null && SUDO=sudo || SUDO=)
  $SUDO apt-get update -qq >/dev/null 2>&1 && \
  $SUDO apt-get install -y -qq --no-install-recommends libreoffice-writer libreoffice-impress \
      fonts-noto-cjk poppler-utils >/dev/null 2>&1 || { echo "LibreOffice unavailable" >&2; exit 2; }
fi
for f in "$@"; do
  dir=$(dirname "$f")
  soffice --headless --convert-to pdf --outdir "$dir" "$f" >/dev/null 2>&1
  pdf="${f%.*}.pdf"
  if [ -f "$pdf" ]; then
    pages=$(pdfinfo "$pdf" 2>/dev/null | awk '/^Pages:/{print $2}')
    printf '%s\t%s\n' "${pages:-?}" "$pdf"
  else
    printf 'FAILED\t%s\n' "$f"
  fi
done
