# Troubleshooting

Tell Claude "this didn't work, fix it" first. These are the fixes it will try.

| Problem | Fix |
|---|---|
| `python3: command not found` (Mac) | Run `xcode-select --install`, click Install, wait, try again. Or install Python 3.12 from python.org. |
| `python` not found (Windows) | `winget install -e --id Python.Python.3.12 --scope user`, or python.org with "Add python.exe to PATH" ticked. Open a new terminal after. |
| "Python 3.10 or newer is needed" | Install Python 3.12 (as above) and run setup with it, e.g. `python3.12 tools/setup.py`. |
| pip fails to install `kokoro-onnx` or `sherpa-onnx` | Update pip: `.venv/bin/python -m pip install -U pip`, then run setup again. On an old Intel Mac, use Python 3.11 or 3.12 from python.org. |
| Download stops halfway | Run setup again; it resumes from what's missing. On a work network, the downloads from github.com may be blocked. |
| "No browser found for rendering" | Setup installs one. If that's blocked, install Google Chrome normally; the kit uses it automatically. |
| Voice sounds too slow / fast | Change `speed` in `settings.json` (1.0 normal, 1.1 to 1.2 is reel pace), then re-voice. |
| Captions out of sync | Run `tools/timing.py <name>` again after any new voice. If you recorded yourself, make `script.md` match what you actually said. |
| "Could not find the words ... in the voiceover" | A scene's `at` doesn't match `script.md`. Copy the words exactly. |
| Emoji show as boxes | Your system lacks an emoji font (rare on Mac/Windows). Use words or an image instead. |
| Render is slow | Use `--draft` while iterating; the final render takes about 3 s of work per second of video. |
| Fish / ElevenLabs error 401 | The API key in `.env` is wrong or expired. 402/429 means the account is out of credits. |
