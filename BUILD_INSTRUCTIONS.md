# Building Capablanca Executable

## Prerequisites

1. **Install PyInstaller:**
   ```bash
   pip install pyinstaller
   ```

2. **Ensure all dependencies are installed:**
   ```bash
   pip install -r requirements.txt
   ```

## Build Single Executable

Run this command from the `python/` directory:

```bash
pyinstaller Capablanca.spec
```

## Output

The executable will be created at:
- **Windows**: `dist/Capablanca.exe`
- **Mac**: `dist/Capablanca` (Unix executable)
- **Linux**: `dist/Capablanca` (Unix executable)

## Distribution

Simply share the executable from the `dist/` folder. Users can run it without installing Python.

**File size**: Approximately 15-20 MB (includes Python runtime, dependencies, and assets)

## Optional: Add an Icon

1. Create or download a `.ico` file (Windows) or `.icns` file (Mac)
2. Save it as `Capablanca.ico` in the `python/` directory
3. Edit `Capablanca.spec` and change:
   ```python
   icon=None,
   ```
   to:
   ```python
   icon='Capablanca.ico',
   ```
4. Rebuild: `pyinstaller Capablanca.spec`

## Troubleshooting

**Missing assets error:**
- Ensure the `images/` folder exists in the python directory
- Check that all PNG files are present in `images/2x/`

**Import errors:**
- Install missing packages with pip
- Add any missing imports to `hiddenimports=[]` in the spec file

**Antivirus false positives:**
- Some antivirus software flags PyInstaller executables
- This is a known issue with all PyInstaller apps
- Users may need to whitelist the executable

## Clean Build

To remove build artifacts:
```bash
# Windows
rmdir /s /q build dist
del Capablanca.spec

# Mac/Linux
rm -rf build dist __pycache__
rm *.spec
```

Then rebuild with `pyinstaller Capablanca.spec`
