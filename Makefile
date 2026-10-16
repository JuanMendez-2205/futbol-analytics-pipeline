.PHONY: all ingest transform viz clean

all: ingest transform viz

ingest:
	python ingest/extract_load.py

transform:
	cd dbt_futbol && dbt build --profiles-dir .

viz:
	python viz/shotmap.py --team Argentina
	python viz/pass_network.py --match 3943077 --team Argentina

clean:
	rm -rf data dbt_futbol/target dbt_futbol/logs
