-- Run against a saved copy of the daily archive, opened read-only.
-- Expected per closed UTC day: 96 successful batches in each of two streams.
SELECT stream, status, COUNT(*) AS batches
FROM gdelt_batches
GROUP BY stream, status
ORDER BY stream, status;

-- Publisher language coverage is not the geography of events.
SELECT language, COUNT(*) AS articles, COUNT(DISTINCT source) AS publishers
FROM gdelt_docs
GROUP BY language
ORDER BY articles DESC
LIMIT 10;
