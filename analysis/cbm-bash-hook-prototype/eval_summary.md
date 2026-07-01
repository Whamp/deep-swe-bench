# CMB bash-hook parser eval
Samples: **2944** real bash calls from 12_v0 configs `baseline, observational-memory-gpt54mini-low, codebase-memory-om, codebase-memory-om-reindex`.
## Command classification
| metric | value |
|---|---:|
| true positive | 953 |
| false positive | 0 |
| false negative | 0 |
| true negative | 1991 |
| precision | 1.000 |
| recall | 1.000 |
| F1 | 1.000 |

## Token/file extraction on positive commands
| target | precision | recall | F1 |
|---|---:|---:|---:|
| search tokens | 0.994 | 0.993 | 0.993 |
| output files (top 8) | 1.000 | 1.000 | 1.000 |

## Label mix
Gold reasons: negative=1991, grep_tokens+grep_output_files=617, grep_tokens=156, grep_output_files=96, small_listing_files=84

Parser decisions: skip_validation_or_mutation=1273, search_with_tokens=776, skip_other=588, skip_listing_no_pattern=103, search_file_output=93, listing_small_file_output=84, search_no_good_token=26, skip_dependency_manifest_search=1

## False positives
None.

## False negatives
None.

## Token misses
- `s00591` baseline/boa-hierarchical-evaluation-cancellation/r0
  - cmd: `grep -R "enqueue_job\|run_jobs\|eval_with\|struct Context\|pub struct Script\|pub struct Module" -n core | head -200`
  - gold: pos=True reason=grep_tokens+grep_output_files tokens=['enqueue_job', 'eval_with', 'run_jobs', 'Context', 'Script', 'Module'] files=['core/engine/src/object/builtins/jspromise.rs', 'core/engine/src/job.rs', 'core/engine/src/context/mod.rs', 'core/runtime/src/interval/tests.rs', 'core/engine/src/builtins/promise/tests.rs']
  - pred: augment=True reason=search_with_tokens tokens=['enqueue_job', 'eval_with', 'run_jobs', 'Context', 'Script'] files=['core/engine/src/object/builtins/jspromise.rs', 'core/engine/src/job.rs', 'core/engine/src/context/mod.rs', 'core/runtime/src/interval/tests.rs', 'core/engine/src/builtins/promise/tests.rs']
- `s00811` observational-memory-gpt54mini-low/actionlint-action-pinning-lint/r2
  - cmd: `grep -n "type Exec interface" -n ast.go`
  - gold: pos=True reason=grep_tokens+grep_output_files tokens=['Exec', 'interface'] files=['ast.go']
  - pred: augment=True reason=search_with_tokens tokens=['interface'] files=['ast.go']
- `s00938` observational-memory-gpt54mini-low/httpx-streaming-json-iteration/r2
  - cmd: `python - <<'PY' import httpx; print(hasattr(httpx,'ByteStream')) PY grep -R "def test_write_timeout" -n tests | head`
  - gold: pos=True reason=grep_tokens tokens=['test_write_timeout', 'ByteStream'] files=[]
  - pred: augment=True reason=search_with_tokens tokens=['test_write_timeout'] files=[]
- `s00993` observational-memory-gpt54mini-low/fastapi-implicit-head-options/r2
  - cmd: `rg "def (include_router|add_api_route|api_route|get\(|head\(|options\()|class APIRouter|class APIRoute" -n fastapi/routing.py fastapi/applications.py`
  - gold: pos=True reason=grep_tokens+grep_output_files tokens=['include_router', 'add_api_route', 'api_route', 'APIRouter', 'APIRoute', 'options'] files=['fastapi/routing.py', 'fastapi/applications.py']
  - pred: augment=True reason=search_with_tokens tokens=['include_router', 'add_api_route', 'api_route', 'APIRouter', 'APIRoute'] files=['fastapi/routing.py', 'fastapi/applications.py']
- `s00994` observational-memory-gpt54mini-low/fastapi-implicit-head-options/r2
  - cmd: `grep -nE "def (include_router|add_api_route|api_route|get\(|head\(|options\()|class APIRouter|class APIRoute" fastapi/routing.py fastapi/applications.py | head -80`
  - gold: pos=True reason=grep_tokens+grep_output_files tokens=['include_router', 'add_api_route', 'api_route', 'APIRouter', 'APIRoute', 'options'] files=['fastapi/routing.py', 'fastapi/applications.py']
  - pred: augment=True reason=search_with_tokens tokens=['include_router', 'add_api_route', 'api_route', 'APIRouter', 'APIRoute'] files=['fastapi/routing.py', 'fastapi/applications.py']
- `s01302` observational-memory-gpt54mini-low/boa-hierarchical-evaluation-cancellation/r0
  - cmd: `rg "Evaluation|eval_with|enqueue_job|run_jobs|struct Context|impl Context|evaluate" core -g'*.rs' | head -200`
  - gold: pos=True reason=grep_tokens tokens=['enqueue_job', 'Evaluation', 'eval_with', 'run_jobs', 'Context', 'evaluate'] files=[]
  - pred: augment=True reason=search_with_tokens tokens=['enqueue_job', 'Evaluation', 'eval_with', 'run_jobs', 'Context'] files=[]
- `s01456` codebase-memory-om/kgateway-consistent-hash-policy/r0
  - cmd: `find /root/go/pkg/mod -path '*envoy/config/route/v3/route_components.pb.go' | head -1 | xargs grep -n "type RouteAction_HashPolicy" | head -80`
  - gold: pos=True reason=grep_tokens tokens=['RouteAction_HashPolicy', 'route_components'] files=[]
  - pred: augment=True reason=search_with_tokens tokens=['RouteAction_HashPolicy'] files=[]
- `s02470` codebase-memory-om-reindex/fastapi-implicit-head-options/r1
  - cmd: `rg "def (include_router|add_api_route|api_route|get\(|head\(|options\()|class APIRoute|class APIRouter|methods" fastapi/routing.py fastapi/applications.py | head -100`
  - gold: pos=True reason=grep_tokens+grep_output_files tokens=['include_router', 'add_api_route', 'api_route', 'APIRouter', 'APIRoute', 'options'] files=['fastapi/routing.py', 'fastapi/applications.py']
  - pred: augment=True reason=search_with_tokens tokens=['include_router', 'add_api_route', 'api_route', 'APIRouter', 'APIRoute'] files=['fastapi/routing.py', 'fastapi/applications.py']
- `s02471` codebase-memory-om-reindex/fastapi-implicit-head-options/r1
  - cmd: `grep -nE "def (include_router|add_api_route|api_route|get\(|head\(|options\()|class APIRoute|class APIRouter" fastapi/routing.py fastapi/applications.py | head -80`
  - gold: pos=True reason=grep_tokens+grep_output_files tokens=['include_router', 'add_api_route', 'api_route', 'APIRouter', 'APIRoute', 'options'] files=['fastapi/routing.py', 'fastapi/applications.py']
  - pred: augment=True reason=search_with_tokens tokens=['include_router', 'add_api_route', 'api_route', 'APIRouter', 'APIRoute'] files=['fastapi/routing.py', 'fastapi/applications.py']
