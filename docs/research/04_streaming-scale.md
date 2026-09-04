# Streaming at TB/PB scale, bounded memory

## Requirement (brief)
Exports can reach terabyte/petabyte scale. Demo must report elapsed, records/s,
bytes/s, and peak memory at >=2 sizes (largest >=10x smallest). Production design
must handle concurrency, skew, and large records.

## Sources
- CSV2GEO — streaming/backpressure & memory (csv.DictReader, chunksize): https://csv2geo.com/blog/how-to-geocode-a-large-file
- Medium (Thinking Loop) — stream large files without killing memory: https://medium.com/@ThinkingLoop/10-ways-to-stream-large-files-without-killing-memory-edbe9b83ba95
- Medium (Gürkan) — streaming large data, small buffers: https://medium.com/@ramazanefegurkan/streaming-large-data-without-breaking-your-memory-1e0a7a1daca5
- superjson.ai — chunked JSON pipelines: https://superjson.ai/blog/2025-08-30-json-performance-optimization-large-files-guide/
- jsonconsole — streaming/chunking large JSON: https://jsonconsole.com/blog/performance-optimization-large-json-datasets-techniques-strategies

## Key findings
- **Whole-file loads are the scale bug.** `pandas.read_csv` of a 1M-row file uses
  ~1.5 GB RAM before any work; `json.loads` and `list(csv.reader)` are O(file).
  The starter loads every file fully — fine for the demo, wrong for the memory
  model it must report. (CSV2GEO)
- **Row-streaming primitives (stdlib):** `csv.reader`/`csv.DictReader` iterate row
  by row; write rows as they are transformed. Bounded memory ≈ one row.
- **NDJSON for streaming JSON:** each line is a complete object; any line can be
  written and flushed independently and the file stays valid even if the writer
  crashes mid-stream. Plain JSON arrays need a streaming parser (e.g. `ijson`) to
  avoid loading the whole document. (superjson, CSV2GEO)
- **SQLite streams naturally:** a server-side cursor (`connection.execute(...)`
  iterated, not `fetchall()`) yields rows without materializing the table.
- **Bound concurrency:** cap in-flight work (p-limit / buffered channel /
  semaphore) and await the bound inside the loop to apply backpressure.

## Implication for our implementation
- Convert each format transformer to **stream rows** and write incrementally:
  `csv.reader` → write per row; SQLite → iterate cursor, `UPDATE` per row in a
  transaction; JSON → keep `json.loads` for the trial (policy inputs are small
  records) but **note `ijson`/NDJSON** as the large-record upgrade in SUBMISSION.
- Report **peak RSS** via `resource.getrusage` (starter already does) and show it
  stays roughly flat as record count scales 10x — that's the evidence the memory
  model is bounded.
- Production: shard by file/partition, one worker per file, bound worker
  concurrency; large single files split by byte-range (CSV line-aligned) — detail
  in `07_cloud-cost-design.md`.
