# matrix.svg

Static Python CLI that emits a fully self-contained Matrix rain SVG animation. The visual stays GPU-friendly by relying on SVG transforms and SMIL animation only—no JavaScript runtime required.

![Matrix rain preview](assets/matrix-preview.svg)

## Requirements
- Python 3.12 or newer
- No third-party dependencies; the script uses the standard library only

## Quick Start
```bash
python generate_matrix_svg.py > matrix.svg
```

With `uv` installed you can also run the project without installing anything:

```bash
uv run matrix-svg > matrix.svg
```

Or launch it ad-hoc via `uvx` from the repo root (zero-install execution):

```bash
uvx --from . matrix-svg > matrix.svg
```

## Packaging / Binary-Style Usage
- Build wheel + source distribution for releases:
	```bash
	uv build
	ls dist/
	```
	The command above emits `dist/matrix_svg-0.1.0-py3-none-any.whl` and `dist/matrix_svg-0.1.0.tar.gz`, ready to upload to GitHub releases or PyPI.
- Install as a personal tool without touching your global site-packages:
	```bash
	uv tool install --from . matrix-svg
	matrix-svg --help
	```
	This drops a runnable `matrix-svg` shim into uv’s tool directory (add it to `PATH` once via `uv tool update-shell`).

Open the resulting `matrix.svg` in any modern browser or SVG-capable viewer. Columns are laid out against a 1000 px base canvas (plus any offset you request) and still scale fluidly to the width of their container.

## Command-Line Options
- `--no-lightning` – disable the periodic lightning overlay.
- `--nice LEVEL` – progressively disable visual flourishes for lower-power devices (0 keeps everything; higher levels strip effects in the order listed when you run `--help`).
- `--gps-min` / `--gps-max` – clamp the glyph count per vertical strand.
- `--columns-regular` / `--columns-irregular` – control the number of evenly spaced and irregularly offset columns, respectively.
- `--width-offset VALUE` – tweak the base canvas width (default 1000 px + VALUE) to spread columns wider or pull them closer together without touching the source code.
- `--preview` – emit the lightweight README preview scene (no lightning, narrow glyph counts, 5 regular + 2 irregular strands, no metadata block).

Use `python generate_matrix_svg.py --help` for the full option reference.

To preview the animation in VS Code, install the “SVG Preview” extension or use `python -m http.server` and open the file in a browser tab.

## How It Works
- Columns and glyph sequences are derived deterministically from seed data to keep the animation dense without bloating the SVG.
- Animations are implemented with `animateTransform` translate/scale cycles, plus optional opacity and blur filters for trailing effects.
- The generator relies on an ElementTree object model, making it easy to extend or reshape the SVG structure programmatically.

## Project Structure
- `generate_matrix_svg.py` – the generator CLI and supporting helpers.
- `pyproject.toml` – project metadata and the `matrix-svg` console entry point.
- `LICENSE` – licensing terms that match the embedded metadata block.
- `main.py` – convenience wrapper for experiments or future UI hooks.
- `pyproject.toml` also exposes `matrix-svg` as a `uv`/`uvx` script for zero-install runs.
- `assets/matrix-preview.svg` – lightweight sample embedded above; regenerate it with `python scripts/make_preview.py` (coming soon) or the inline command below.

```bash
python generate_matrix_svg.py --preview > assets/matrix-preview.svg
```

## Development Notes
- Run `matrix-svg` after installing the project (e.g., `pip install .`) to execute via the registered console script.
- The code supports toggling visual features via the “nice” levels; when adding new effects, update the `NICE_FEATURE_STEPS` list to keep the CLI documentation accurate.
- Generated SVGs can be large; commit only representative samples when needed, and prefer regenerating locally from the CLI.

Contributions that further reduce SVG duplication, improve accessibility, or add preset scenes are welcome. Open an issue or PR with your ideas.
