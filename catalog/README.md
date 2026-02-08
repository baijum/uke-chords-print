# Chord Sheet Catalog

A collection of pre-made chord sheet files organized by category. Each file can be fed directly into `uke-chords-print` to generate a printable PDF.

## Quick Start

```bash
# Generate a PDF from any catalog file
python3 -m uke_chords_print --file catalog/songs/beginner_hits.txt -t "Beginner Hits"

# Combine multiple files
python3 -m uke_chords_print \
  --file catalog/progressions/pop_anthems.txt \
  --file catalog/progressions/50s_doo_wop.txt \
  -t "Common Progressions"
```

## Categories

### Chord Progressions (`progressions/`)

Named chord progressions in multiple keys -- the building blocks of music.

| File | Progression | Keys | Example Songs |
|------|-------------|------|---------------|
| [pop_anthems.txt](progressions/pop_anthems.txt) | I-V-vi-IV | C, G | Let It Be, I'm Yours, Someone Like You |
| [50s_doo_wop.txt](progressions/50s_doo_wop.txt) | I-vi-IV-V | C, G | Stand By Me, Earth Angel, Blue Moon |
| [12_bar_blues.txt](progressions/12_bar_blues.txt) | 12-bar blues | C, G, A | Johnny B. Goode, Hound Dog |
| [classic_rock.txt](progressions/classic_rock.txt) | I-IV-V, i-bVII-bVI-V | C, G, Am | La Bamba, Sweet Home Alabama |
| [jazz_essentials.txt](progressions/jazz_essentials.txt) | ii-V-I, I-vi-ii-V | C, G, F | Jazz standards, I Got Rhythm |

### Hit Songs (`songs/`)

Chords grouped by song -- print a sheet for your practice session.

| File | Level | Songs Included |
|------|-------|----------------|
| [beginner_hits.txt](songs/beginner_hits.txt) | 2-4 chords | Riptide, Stand By Me, I'm Yours, Let It Be, Three Little Birds, You Are My Sunshine, Somewhere Over the Rainbow |
| [pop_classics.txt](songs/pop_classics.txt) | 4-6 chords | Hallelujah, Can't Help Falling in Love, Country Roads, Hey Jude, Don't Stop Believin' |
| [campfire_songs.txt](songs/campfire_songs.txt) | 3-4 chords | This Land Is Your Land, Blowin' in the Wind, Lean on Me, Puff the Magic Dragon |

### Classical Music (`classical/`)

| File | Pieces Included |
|------|-----------------|
| [classical_pieces.txt](classical/classical_pieces.txt) | Ode to Joy (Beethoven), Pachelbel Canon, Amazing Grace, Greensleeves, Auld Lang Syne, Jesu Joy of Man's Desiring (Bach), Morning Mood (Grieg) |

### World Music (`world/`)

Songs and styles from around the globe.

| File | Region/Style | Songs Included |
|------|-------------|----------------|
| [latin_bossa.txt](world/latin_bossa.txt) | Latin America, Brazil | La Bamba, Guantanamera, Cielito Lindo, Chan Chan, Besame Mucho, Girl from Ipanema |
| [island_hawaiian.txt](world/island_hawaiian.txt) | Hawaii, Reggae, Island | Aloha Oe, IZ's Over the Rainbow, Three Little Birds, No Woman No Cry, Don't Worry Be Happy |
| [folk_traditions.txt](world/folk_traditions.txt) | Global folk | Greensleeves (England), Hava Nagila (Israel), Sakura (Japan), Danny Boy (Ireland), Arirang (Korea), Kalinka (Russia), Waltzing Matilda (Australia) |

## Notes

- These files contain **chords only** (no lyrics, no tabs). They are designed to give you a printable reference of the finger positions you need.
- Each song section lists the unique chords used in that song. If multiple songs share the same chords, the duplicates still appear in the PDF -- useful context when practicing.
- All chords are looked up from the built-in database, so every voicing includes finger positions, note names, and inversion labels.
- Files can be combined: pass multiple `--file` flags or list chord names alongside a file.
