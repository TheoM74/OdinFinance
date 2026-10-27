# Design

Two themes share one QSS template (`resources/style.qss`) and one set of components (`views/widgets.py`). Tokens live in `views/theme.py`; never hard-code a colour in a widget.

## Layout

- Header bar: logo, navigation tabs (Synthèse, Journal, Paramètres), association and year, theme switch, primary « Exporter le bilan ».
- Pages: 28 px side margins, 24 px top, 18–20 px between panels. Content sits in `Panneau` containers (20 px padding).
- Journal: fixed 400 px entry form on the left (fields scroll when the window is short), operations table on the right.
- Minimum window 1080 × 680.

## Tokens

| Token | Cyberpunk | Classique | Use |
|---|---|---|---|
| fond | #160000 | #f3f5f8 | window ground |
| surface | #200404 | #ffffff | panels, header, tables |
| surface_alt | #250606 | #f8fafc | alternate rows |
| survol | #340d0d | #edf1f6 | hover |
| texte | #ecdede | #18212c | body text |
| texte_doux | #c4a9a9 | #556170 | labels, help |
| titre | #ff9393 | #18212c | page and panel titles |
| accent | #5aedf4 | #0070c0 | primary action, current tab, selection |
| danger | #ff5c5c | #c42b1c | errors, negative amounts, delete |
| positif | #98c379 | #107c41 | positive amounts |
| trait / trait_fort | salmon 20 % / 50 % | #dfe4ea / #b9c3ce | borders |
| focus | #ff5c5c | #0070c0 | keyboard focus ring (2 px) |
| rayon | 0 | 6 px | corner radius |

## Typography

- Cyberpunk: logo in Cyberpunk (uppercase letters only, no accents or digits), titles, labels and buttons in Oxanium SemiBold uppercase with 6 % tracking, body in Blender Pro 16 px.
- Classique: system UI font (Segoe UI / San Francisco), 14 px body, semibold titles, sentence case.
- Table column headers are small uppercase labels in both themes.

## Signature details (Cyberpunk only)

- Panels with the top-right corner cut at 14 px.
- Panel titles underlined by a salmon bar with a notch at 18 % (from the portfolio's section titles).
- Logo with a 3 px cyan offset shadow.
- Window ground with faint scanlines and a 64 px grid.

## Components and states

- Buttons: default (outlined), `primaire` (filled accent), `danger` (red outline), `discret` (text only), `segment` (exclusive choice), `icone`. Every button has hover, pressed, keyboard focus and disabled states; focus only shows for keyboard navigation.
- Fields: label above, « · facultatif » suffix for optional fields, error message under the field and red border (`erreur` property).
- Amounts: French format `1 234,56 €`, signed and coloured in the journal, right-aligned.
- Empty states explain the next action (journal, summary tables, accounts).
- Icons: hand-drawn SVG, 24 px grid, 2 px round stroke (`views/icones.py`), recoloured per theme. No emoji.
