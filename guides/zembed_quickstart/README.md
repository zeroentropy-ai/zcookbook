# zembed-1 Embedding API Guide

This notebook shows how to use `zclient.models.embed()` to get embedding vectors from text. It walks through every parameter and includes two hands-on examples (sentence similarity and clustering).

## What's covered

1. Basic usage: embed a list of strings and inspect the response
2. Full parameter reference (`model`, `input`, `input_type`, `dimensions`, `encoding_format`, `latency`)
3. Asymmetric retrieval: separate query and document embeddings for search
4. Dimension projections: pick your vector size (40, 80, 160, 320, 640, 1280, 2560)
5. Latency modes: `"fast"` for real-time, `"slow"` for batch
6. Sentence similarity with cosine distance (numpy)
7. Clustering with KMeans (scikit-learn)

## Prerequisites

- Python 3.12+
- ZeroEntropy API key (set as `ZEROENTROPY_API_KEY` environment variable)

## Run the notebook

```bash
uv sync
jupyter notebook zembed_api_guide.ipynb
```

## Quick example

```python
from zeroentropy import ZeroEntropy

zclient = ZeroEntropy()

response = zclient.models.embed(
    model="zembed-1",
    input=["Your text string goes here"],
    input_type="query",
    dimensions=640,
)

vec = response.results[0].embedding  # list of 640 floats
```
