# API Reference

Complete reference for the DataFlow SDK. All classes and methods are available under the `dataflow` package.

---

## Pipeline

### `Pipeline(name: str, config: Optional[Config] = None)`

Create a new pipeline instance. The `name` parameter is used for logging and dashboard identification.

### `Pipeline.source(source: Source) -> Stream`

Attach a data source to the pipeline and return a Stream handle.

### `Pipeline.run(blocking: bool = True)`

Start the pipeline. If `blocking=True`, the call will not return until the pipeline is stopped or encounters a fatal error.

### `Pipeline.stop()`

Gracefully shut down the pipeline, flushing all in-flight records and committing state checkpoints.

---

## Stream

### `Stream.map(fn: Callable) -> Stream`

Apply a one-to-one transformation to each record in the stream.

### `Stream.flat_map(fn: Callable) -> Stream`

Apply a one-to-many transformation. The function should return an iterable.

### `Stream.filter(fn: Callable) -> Stream`

Keep only records for which the function returns `True`.

### `Stream.window(window: Window) -> WindowedStream`

Group records into time-based or count-based windows for aggregation.

### `Stream.sink(sink: Union[Sink, Callable])`

Write records to an external system or callable.

---

## Windows

### `Tumbling(seconds: int)`

Fixed-size, non-overlapping time windows. Each record belongs to exactly one window.

### `Sliding(size_seconds: int, slide_seconds: int)`

Overlapping windows of a given size that advance by `slide_seconds`. Records may belong to multiple windows.

### `Session(gap_seconds: int)`

Dynamic windows that close after a period of inactivity. Useful for sessionizing user activity.

---

## Authentication

All API calls require a valid API key. Set the `DATAFLOW_API_KEY` environment variable or pass it directly:

```python
from dataflow import Pipeline, Config

config = Config(api_key="your-api-key-here")
pipeline = Pipeline("secure-pipeline", config=config)
```

API keys can be generated from the DataFlow Dashboard under Settings > API Keys. Each key has configurable rate limits and permissions scoped to specific pipelines or namespaces.
