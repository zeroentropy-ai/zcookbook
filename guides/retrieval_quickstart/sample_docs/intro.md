# Introduction to DataFlow

DataFlow is an open-source data pipeline framework designed for real-time stream processing and batch analytics. It enables teams to build reliable, scalable data workflows that connect to hundreds of data sources.

## Why DataFlow?

Traditional ETL tools struggle with modern data volumes. DataFlow was built from the ground up to handle millions of events per second while maintaining exactly-once processing guarantees. Whether you're building a recommendation engine, monitoring infrastructure metrics, or aggregating financial transactions, DataFlow provides the primitives you need.

## Key Concepts

- **Streams** are unbounded sequences of records flowing through the pipeline.
- **Transforms** are stateless or stateful operations applied to each record.
- **Windows** group records by time intervals for aggregation.
- **Sinks** write processed data to external systems like databases or object stores.

## Architecture Overview

DataFlow uses a distributed architecture with a control plane and worker nodes. The control plane manages job scheduling and fault recovery, while workers execute transforms in parallel across partitions. State is checkpointed to durable storage, enabling seamless recovery from failures without data loss.

## Getting Started

To install DataFlow, run `pip install dataflow-sdk`. You'll need Python 3.10 or later. Create your first pipeline in under five minutes by following the Quickstart Tutorial.
