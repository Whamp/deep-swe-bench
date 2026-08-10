# read-long-lines@1.0.0

Versioned Pi config that replaces only the built-in `read` tool.

Ordinary read results keep the first 2,000 Unicode code points of each longer
line and append a recovery notice. A focused `read` with `limit=1` delegates to
Pi unchanged and returns the complete line. The override delegates path
resolution, images, errors, cancellation, line limits, byte limits, continuation
notices, and rendering to Pi's exported `createReadToolDefinition`.

The extension appends `read-long-lines.telemetry` custom session entries when it
loads and when it shortens a result. Pi excludes custom entries from model
context. The telemetry records line numbers and character counts but never raw
line content.

This config adds no system preamble, orchestration file, appended system prompt,
skill, secondary model, or nested model call. Its only model role is the main Pi
executor. Executor usage comes from native `session/*.jsonl` assistant messages.

The release has five leaves:

- `gpt-5.6-sol/low`
- `gpt-5.6-terra/low`
- `gpt-5.6-luna/low`
- `deepseek-v4-flash-0731/low`
- `glm-5.2/max`

The DeepSeek leaf pins the exact dated OpenRouter slug, DeepSeek's FP8 endpoint,
no fallbacks, `temperature=1.0`, and `top_p=0.95`. The GLM leaf uses direct Z.ai,
not OpenRouter.
