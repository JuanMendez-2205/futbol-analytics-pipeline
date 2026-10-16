"""
Red de pases de un equipo en un partido, con betweenness centrality.

- Aristas: pases completados entre dos jugadores (marts.pass_network_edges).
- Posición de cada jugador: promedio de dónde dio sus pases.
- Tamaño del nodo: betweenness = qué tan "puente" es el jugador en la circulación.

Uso:
    python viz/pass_network.py                               # final ARG vs COL
    python viz/pass_network.py --match 3943077 --team Colombia
"""

import argparse
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
from adjustText import adjust_text
from mplsoccer import Pitch

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "futbol.duckdb"
OUT_DIR = ROOT / "docs" / "img"
MIN_PASSES = 4  # ignorar conexiones con menos pases para que el gráfico se lea


def main(match_id: int, team: str) -> Path:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    edges = con.execute(
        "SELECT passer, recipient, passes FROM marts.pass_network_edges "
        "WHERE match_id = ? AND team = ? AND passes >= ?",
        [match_id, team, MIN_PASSES],
    ).df()
    # Posición promedio de cada jugador + su apodo (stg_players) para el rótulo.
    positions = con.execute(
        "SELECT p.player, coalesce(pl.display_name, p.player) AS label, "
        "       avg(p.x) AS x, avg(p.y) AS y "
        "FROM staging.stg_passes p "
        "LEFT JOIN staging.stg_players pl ON pl.player = p.player AND pl.team = p.team "
        "WHERE p.match_id = ? AND p.team = ? AND p.is_completed "
        "GROUP BY p.player, label",
        [match_id, team],
    ).df().set_index("player")
    title = con.execute(
        "SELECT home_team || ' ' || home_score || '-' || away_score || ' ' || away_team "
        "       || ' · ' || stage FROM staging.stg_matches WHERE match_id = ?",
        [match_id],
    ).fetchone()[0]
    con.close()
    if edges.empty:
        raise SystemExit("Sin datos para ese partido/equipo.")

    # Grafo dirigido. Para betweenness el peso se interpreta como DISTANCIA,
    # así que usamos 1/pases: más pases entre dos jugadores = más "cerca".
    G = nx.DiGraph()
    for e in edges.itertuples():
        G.add_edge(e.passer, e.recipient, passes=e.passes, dist=1 / e.passes)
    betweenness = nx.betweenness_centrality(G, weight="dist")

    players = positions.loc[positions.index.intersection(list(G.nodes))].copy()
    players["central"] = players.index.map(betweenness).fillna(0)

    print("Top 5 'puentes' (betweenness):")
    for _, row in players.sort_values("central", ascending=False).head(5).iterrows():
        print(f"  {row.label:22s} {row.central:.3f}")

    pitch = Pitch(pitch_type="statsbomb", pitch_color="#1a1a1a", line_color="#888")
    fig, ax = pitch.draw(figsize=(12, 8))
    fig.set_facecolor("#1a1a1a")

    for e in edges.itertuples():
        if e.passer in players.index and e.recipient in players.index:
            a, b = players.loc[e.passer], players.loc[e.recipient]
            pitch.lines(a.x, a.y, b.x, b.y, lw=e.passes * 0.45,
                        color="#6cace4", alpha=0.55, zorder=1, ax=ax)

    pitch.scatter(players.x, players.y, s=players.central * 5000 + 250,
                  color="#ffd700", edgecolors="black", zorder=2, ax=ax)
    # Rótulos: adjust_text los separa si se pisan (ej. Messi y Julián Álvarez).
    labels = [ax.text(row.x, row.y - 4.5, row.label, color="white",
                      ha="center", va="center", fontsize=9, zorder=3)
              for _, row in players.iterrows()]
    adjust_text(labels, ax=ax, arrowprops=dict(arrowstyle="-", color="white", lw=0.4))

    ax.set_title(f"{team} — red de pases\n{title}\n"
                 f"tamaño del nodo = betweenness centrality · mínimo {MIN_PASSES} pases por conexión",
                 color="white", fontsize=13)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"pass_network_{match_id}_{team.lower().replace(' ', '_')}.png"
    fig.savefig(out, dpi=120, bbox_inches="tight", facecolor="#1a1a1a")
    print(f"Guardado {out}")
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--match", type=int, default=3943077, help="3943077 = final ARG vs COL")
    parser.add_argument("--team", default="Argentina")
    args = parser.parse_args()
    main(args.match, args.team)
