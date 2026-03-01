# Quickstart Tutorial

This tutorial walks you through building your first DataFlow pipeline: a real-time word counter that processes a stream of text messages.

## Prerequisites

- Python 3.10 or later
- DataFlow SDK installed (`pip install dataflow-sdk`)
- A running DataFlow cluster or local development mode

## Step 1: Define a Source

Sources read data into the pipeline. For this tutorial, we'll use a built-in generator source that produces random sentences:

```python
from dataflow import Pipeline, sources

pipeline = Pipeline("word-counter")
stream = pipeline.source(sources.RandomSentences(rate=100))
```

## Step 2: Apply Transforms

Transforms process records one at a time or in batches. We'll split sentences into words, lowercase them, and count occurrences in a tumbling window:

```python
from dataflow import transforms, windows

words = stream.flat_map(lambda sentence: sentence.split())
words = words.map(lambda word: (word.lower(), 1))
counts = words.window(windows.Tumbling(seconds=10)).reduce_by_key(sum)
```

## Step 3: Write to a Sink

Sinks push results to external systems. Here we'll print to the console:

```python
counts.sink(print)
pipeline.run()
```

## Step 4: Monitor the Pipeline

Open the DataFlow dashboard at `http://localhost:8080` to see throughput, latency percentiles, and backpressure metrics in real time. The dashboard also shows per-transform resource utilization.

## Error Handling

DataFlow automatically retries failed records up to three times. For records that exceed the retry limit, you can configure a dead-letter queue:

```python
pipeline.set_dead_letter_sink(sources.FileSystem("/tmp/dlq"))
```

## Next Steps

Now that you've built a basic pipeline, explore the Advanced Guide to learn about stateful transforms, exactly-once semantics, and multi-region deployments.
