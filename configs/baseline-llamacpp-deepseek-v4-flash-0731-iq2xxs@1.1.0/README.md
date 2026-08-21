# baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.1.0

Pi 0.84.1 compatibility release for the canonical server60 Antirez IQ2_XXS
DeepSeek V4 Flash 0731 service at `http://100.92.238.117:8033/v1`.

This release changes no model or request behavior from 1.0.0. It retains:

- model `deepseek-v4-flash-0731-q8-fast-prefill`;
- 430,080-token context, one server slot, and 65,536-token completion cap;
- max thinking through the llama.cpp chat-template arguments;
- temperature 1.0, top-p 0.95, top-k 0, min-p 0, and repeat penalty 1;
- the audited 360-second default bash timeout;
- local-compute-only execution with native Pi session usage.

Only the max-thinking leaf is carried forward because M8 uses max thinking. The
release exists to compare GGUF-TP and canonical llama.cpp under the same pinned
Pi 0.84.1 subject.
