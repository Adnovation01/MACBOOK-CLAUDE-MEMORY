import os
import pytest
import tempfile


def save_env_logic(updates: dict, env_path: str):
    """Copy of _save_env from app.py — tests the algorithm in isolation."""
    lines = []
    if os.path.exists(env_path):
        with open(env_path) as f:
            lines = f.readlines()
    existing = {}
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and '=' in stripped:
            key = stripped.split('=', 1)[0].strip()
            existing[key] = i
    for key, value in updates.items():
        if key in existing:
            lines[existing[key]] = f'{key}={value}\n'
        else:
            lines.append(f'{key}={value}\n')
    with open(env_path, 'w') as f:
        f.writelines(lines)


def test_creates_new_key():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write('EXISTING=old\n')
        path = f.name
    try:
        save_env_logic({'NEW_KEY': 'new_value'}, path)
        content = open(path).read()
        assert 'NEW_KEY=new_value' in content
        assert 'EXISTING=old' in content
    finally:
        os.unlink(path)


def test_updates_existing_key():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write('EMAIL_USER=old@gmail.com\n')
        path = f.name
    try:
        save_env_logic({'EMAIL_USER': 'new@gmail.com'}, path)
        content = open(path).read()
        assert 'EMAIL_USER=new@gmail.com' in content
        assert 'old@gmail.com' not in content
    finally:
        os.unlink(path)


def test_handles_missing_file():
    path = '/tmp/test_missing_env_xyz123.env'
    if os.path.exists(path):
        os.unlink(path)
    save_env_logic({'KEY': 'val'}, path)
    assert os.path.exists(path)
    assert 'KEY=val' in open(path).read()
    os.unlink(path)


def test_preserves_comments():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write('# Gmail config\nEMAIL_USER=x@gmail.com\n')
        path = f.name
    try:
        save_env_logic({'EMAIL_USER': 'y@gmail.com'}, path)
        content = open(path).read()
        assert '# Gmail config' in content
        assert 'EMAIL_USER=y@gmail.com' in content
    finally:
        os.unlink(path)
