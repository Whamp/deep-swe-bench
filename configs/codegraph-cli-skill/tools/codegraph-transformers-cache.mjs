import { env } from '@huggingface/transformers';

// Transformers.js defaults its cache to its package directory. In benchmark
// cells the config is mounted read-only at /arm, so semantic embedding commands
// need an explicit writable cache.
env.cacheDir = process.env.CODEGRAPH_TRANSFORMERS_CACHE || '/tmp/codegraph-transformers-cache';
