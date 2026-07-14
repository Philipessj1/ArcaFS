from pathlib import Path

def cleanup_temp_file(path: Path) -> None:
    # Remove a temp file after response
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass