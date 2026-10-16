"""
Shot map de un equipo en el torneo, leyendo de la capa marts (marts.fct_shots).
Tamaño del punto = xG del remate. Estrella dorada = gol.

Uso:
    python viz/shotmap.py --team Argentina
"""

import argparse
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")  # sin ventana: sirve para correr en CI / servidor
import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "futbol.duckdb"
OUT_DIR = ROOT / "docs" / "img"


def main(team: str) -> Path:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    shots = con.execute(
        "SELECT x, y, xg, is_goal FROM marts.fct_shots WHERE team = ?", [team]
    ).df()
    con.close()
    if shots.empty:
        raise SystemExit(f"No hay remates para '{team}'. ¿Corriste el pipeline?")

    xg_total, goals = shots.xg.sum(), int(shots.is_goal.sum())

    pitch = VerticalPitch(pitch_type="statsbomb", half=True,
                          pitch_color="#1a1a1a", line_color="#888")
    fig, ax = pitch.draw(figsize=(8, 10))
    fig.set_facecolor("#1a1a1a")

    misses, scored = shots[~shots.is_goal], shots[shots.is_goal]
    pitch.scatter(misses.x, misses.y, s=misses.xg * 900 + 60, color="#6cace4",
                  edgecolors="white", linewidth=0.5, alpha=0.75, ax=ax, zorder=2)
    pitch.scatter(scored.x, scored.y, s=scored.xg * 900 + 120, marker="*",
                  color="#ffd700", edgecolors="white", linewidth=1.2, ax=ax, zorder=3)

    ax.set_title(f"{team} — Copa América 2024\n{len(shots)} remates · {goals} goles · "
                 f"xG {xg_total:.2f} (sin tanda de penales)",
                 color="white", fontsize=13, pad=12)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"shotmap_{team.lower().replace(' ', '_')}.png"
    fig.savefig(out, dpi=120, bbox_inches="tight", facecolor="#1a1a1a")
    print(f"Guardado {out}")
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--team", default="Argentina")
    main(parser.parse_args().team)
