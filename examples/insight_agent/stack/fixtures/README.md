# Fixtures

`init.sql` creates the sample `city_metrics` table the insight agent reads. The compose file mounts it into Postgres on first start. The agent does not own a second schema.
