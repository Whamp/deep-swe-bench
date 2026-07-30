Every `bash` call must include a `timeout`. Without one, a hung command can block you indefinitely and prevent further work. Choose a limit appropriate to the command:

```json
{"command": "pytest tests/", "timeout": 600}
```
