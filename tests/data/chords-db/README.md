# chords-db ukulele data

`ukulele.json` is the ukulele database from
[tombatossals/chords-db](https://github.com/tombatossals/chords-db)
(`lib/ukulele.json`) at commit
[`df06fa7`](https://github.com/tombatossals/chords-db/tree/df06fa7b425cf5fd29485ff6591236b3557e3fac).
It is MIT licensed (see [`LICENSE`](LICENSE)) and was compiled by hand
independently of this project. It covers 12 keys × 46 chord types in
standard GCEA tuning, with up to four shapes each (2,114 shapes in total),
listed in the order a chord chart would show them.

`fetch.py` downloads the same commit again and checks the SHA-256 against
the one recorded below, so the tests always run against known data:

```bash
python3 tests/data/chords-db/fetch.py
```

SHA-256 of `ukulele.json`:
`233b7018ec35785a8bfa985bad90f4745cee04614c0fd1d5b819cff7406ec601`

## Format

Each shape gives `frets` relative to `baseFret` (`1` is `baseFret`,
`0` is open, `-1` is muted), `fingers`, and the `midi` pitch of each
sounding string, all in G-C-E-A order.

## Errata

The tests check every shape against the interval formulas in
`tests/support.py`. These entries have notes outside their chord and are
excluded (`support.CHORDS_DB_ERRATA`):

| Chord | Shapes | Problem |
|-------|--------|---------|
| Bmadd9 | `2002`, `5452`, `4453` | Notes of another chord (b9, 11, b7 against B) |
| F11 | `1220` | Has F#, G# and D (b9, #9, 13 against F) |

Two shapes have crossed fingers (a lower-numbered finger on a higher fret);
their notes are fine, so only the fingering check skips them
(`support.CHORDS_DB_FINGERING_ERRATA`):

| Chord | Shape | Fingers |
|-------|-------|---------|
| Abmaj11 | `5764` | `2134` |
| Eb alt | `8756` | `3412` |
