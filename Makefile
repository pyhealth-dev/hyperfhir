mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
current_dir := $(dir $(mkfile_path))
current_dir_name := $(notdir $(patsubst %/,%,$(current_dir)))
pg_data_dir := $(current_dir)var/postgresql/data
pg_version := 12.4-alpine
es_version := 7.9.3
esdata_dir := $(current_dir)var/elasticsearch/data

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

run-es:
	docker run --rm \
	-v $(esdata_dir):/usr/share/elasticsearch/data \
	-e "cluster.name=docker-cluster" \
	-e "ES_JAVA_OPTS=-Xms1024m -Xmx1024m" \
	-e "cluster.routing.allocation.disk.threshold_enabled=false" \
	-e "network.publish_host=127.0.0.1" \
	-e "transport.publish_port=9200" \
	-p 127.0.0.1:9200:9200 \
	--name elasticsearch_hyperfhir_dev \
	docker.elastic.co/elasticsearch/elasticsearch-oss:$(es_version)
