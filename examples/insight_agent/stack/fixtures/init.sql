CREATE TABLE city_metrics (
    city TEXT NOT NULL,
    quarter TEXT NOT NULL,
    index_value DOUBLE PRECISION NOT NULL
);

INSERT INTO city_metrics (city, quarter, index_value) VALUES
    ('Pune', '2026Q1', 1.4),
    ('Mumbai', '2026Q1', 1.0),
    ('Nagpur', '2026Q1', 0.8);
