---
title: 故障排除
description: Narrafiilm 常见问题的详细解决方案。
---

# 故障排除

## Installation Issues

### PyQt6 vs PySide6 Conflict

**Error:**
```
QLabel(...): argument 1 has unexpected type 'str'
```

**Solution:**
```bash
pip uninstall PySide6 PySide2
pip install PyQt6
```

### FFmpeg Not Found

**Error:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'
```

**Solution:**

1. Install FFmpeg:
   - macOS: `brew install ffmpeg`
   - Ubuntu: `sudo apt install ffmpeg`
   - Windows: Download from ffmpeg.org

2. Add to system PATH

3. Verify: `ffmpeg -version`

### Module Not Found

**Error:**
```
ModuleNotFoundError: No module named 'PyQt6'
```

**Solution:**
```bash
pip install PyQt6
pip install -r requirements.txt
```

## Runtime Issues

### Application Won't Start

1. Check Python version: `python --version` (need 3.9+)
2. Verify FFmpeg is installed: `ffmpeg -version`
3. Check `.env` file exists with valid API keys
4. Run with debug output: `python main.py --debug`

### AI API Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid API key | Check your API key in `.env` |
| `429 Rate Limited` | Too many requests | Wait and retry, or upgrade plan |
| `500 Server Error` | Provider issue | Try a different provider |

### Video Processing Errors

- **Corrupt video file**: Ensure source video is not corrupted
- **Unsupported format**: Convert to MP4 or MOV first
- **Out of memory**: Reduce video resolution or close other apps

## Performance Issues

### Slow Processing

- Use SSD for project files
- Close other resource-heavy applications
- Reduce preview quality during editing
- Use hardware acceleration if available

### High Memory Usage

- Split long videos into shorter segments
- Clear cache: `Edit > Preferences > Clear Cache`
- Reduce number of open projects

## Export Issues

### Export Fails

1. Check available disk space
2. Verify output directory is writable
3. Ensure no special characters in output filename
4. Try a different export format

### Wrong Export Format

Make sure to select the correct format in export settings:
- **JianYing (剪映)**: Draft JSON
- **Premiere**: XML
- **Final Cut**: FCPXML
- **Standard**: MP4 (H.264/H.265)

## Getting Help

If you're still stuck:

1. Check the [FAQ](../faq)
2. Search [GitHub Issues](https://github.com/Agions/Narrafiilm/issues)
3. Create a new issue with:
   - Your OS and version
   - Python version
   - Full error message
   - Steps to reproduce
