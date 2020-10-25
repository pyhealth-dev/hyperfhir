mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
current_dir := $(dir $(mkfile_path))
current_dir_name := $(notdir $(patsubst %/,%,$(current_dir)))
pg_data_dir := $(current_dir)var/postgresql/data
pg_version := 12.4-alpine

run-pg:
	docker run -i --rm \
	-p 5432:5432 \
	-e POSTGRES_USER=hyperfhir_dm \
	-e POSTGRES_PASSWORD=MyPGSecret \
	-e POSTGRES_HOST_AUTH_METHOD=password \
	-e POSTGRES_DB=hyperfhir_db \
	-e PGDATA=/var/lib/postgresql/data/pgdata \
	-v $(pg_data_dir):/var/lib/postgresql/data \
	--name pg_hyperfhir_tester \
	-t postgres:$(pg_version)
