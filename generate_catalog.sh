#!/bin/bash
# Generate PDFs for all catalog chord sheets.
# Output goes to catalog/pdf/ which is git-ignored.

set -e

OUTDIR="catalog/pdf"
mkdir -p "$OUTDIR"

echo "Generating catalog PDFs..."

for f in catalog/progressions/*.txt catalog/songs/*.txt catalog/classical/*.txt catalog/world/*.txt; do
    name=$(basename "$f" .txt)
    title=$(head -1 "$f" | sed 's/^# *//')
    out="$OUTDIR/$name.pdf"
    echo "  $f -> $out"
    python3 -m uke_chords_print --file "$f" -t "$title" -o "$out"
done

echo "Done. PDFs saved to $OUTDIR/"
