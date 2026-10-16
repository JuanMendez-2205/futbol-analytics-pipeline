"""
Extract + Load: baja datos abiertos de StatsBomb y los carga crudos en DuckDB.

La idea es ELT: acá NO se transforma nada. Los JSON se guardan tal cual
(una fila por partido / por evento, con el JSON original en una columna)
y toda la limpieza y el modelado se hace después con dbt.

Uso:
    python ingest/extract_load.py                      # Copa América 2024 completa
    python ingest/extract_load.py --competition 43 --season 106   # Mundial 2022
    python ingest/extract_load.py --max-matches 3      # prueba rápida (CI)
"""

import argparse
import json
import time
import urllib.request
from pathlib import Path

import duckdb

BASE_URL = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
DB_PATH = ROOT / "data" / "futbol.duckdb"


def fetch_json(url: str, cache_path: Path, retries: int = 3):
    """Descarga un JSON y lo cachea en disco para no pedirlo dos veces."""
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))

    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(data), encoding="utf-8")
            return data
        except Exception as exc:  # red inestable: reintento con espera
            if attempt == retries:
                raise
            print(f"  reintento {attempt} para {url}: {exc}")
            time.sleep(2 * attempt)


def create_raw_tables(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    con.execute("""
        CREATE TABLE IF NOT EXISTS raw.matches (
            match_id   BIGINT PRIMARY KEY,
            competition_id INTEGER,
            season_id  INTEGER,
            payload    JSON,
            loaded_at  TIMESTAMP DEFAULT current_timestamp
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS raw.lineups (
            match_id   BIGINT,
            team       VARCHAR,
            payload    JSON,
            loaded_at  TIMESTAMP DEFAULT current_timestamp,
            PRIMARY KEY (match_id, team)
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS raw.events (
            event_id   VARCHAR PRIMARY KEY,
            match_id   BIGINT,
            payload    JSON,
            loaded_at  TIMESTAMP DEFAULT current_timestamp
        )
    """)


def load(competition_id: int, season_id: int, max_matches: int | None) -> None:
    matches_url = f"{BASE_URL}/matches/{competition_id}/{season_id}.json"
    matches = fetch_json(matches_url, RAW_DIR / "matches" / f"{competition_id}_{season_id}.json")
    if max_matches:
        matches = matches[:max_matches]
    print(f"{len(matches)} partidos para competition={competition_id} season={season_id}")

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))
    create_raw_tables(con)

    # Carga idempotente: si un partido ya estaba, se reemplaza (re-correr no duplica).
    for m in matches:
        con.execute(
            "INSERT OR REPLACE INTO raw.matches (match_id, competition_id, season_id, payload) VALUES (?, ?, ?, ?)",
            [m["match_id"], competition_id, season_id, json.dumps(m)],
        )

    for i, m in enumerate(matches, start=1):
        mid = m["match_id"]
        events = fetch_json(f"{BASE_URL}/events/{mid}.json", RAW_DIR / "events" / f"{mid}.json")
        con.execute("DELETE FROM raw.events WHERE match_id = ?", [mid])
        con.executemany(
            "INSERT INTO raw.events (event_id, match_id, payload) VALUES (?, ?, ?)",
            [(e["id"], mid, json.dumps(e)) for e in events],
        )
        lineups = fetch_json(f"{BASE_URL}/lineups/{mid}.json", RAW_DIR / "lineups" / f"{mid}.json")
        for team in lineups:
            con.execute(
                "INSERT OR REPLACE INTO raw.lineups (match_id, team, payload) VALUES (?, ?, ?)",
                [mid, team["team_name"], json.dumps(team)],
            )
        print(f"  [{i}/{len(matches)}] {m['home_team']['home_team_name']} vs "
              f"{m['away_team']['away_team_name']}: {len(events)} eventos")

    total = con.execute("SELECT count(*) FROM raw.events").fetchone()[0]
    print(f"Listo. raw.events tiene {total} filas -> {DB_PATH}")
    con.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Carga StatsBomb Open Data en DuckDB (capa raw)")
    parser.add_argument("--competition", type=int, default=223, help="competition_id (223 = Copa América)")
    parser.add_argument("--season", type=int, default=282, help="season_id (282 = 2024)")
    parser.add_argument("--max-matches", type=int, default=None, help="limitar partidos (para pruebas)")
    args = parser.parse_args()
    load(args.competition, args.season, args.max_matches)
