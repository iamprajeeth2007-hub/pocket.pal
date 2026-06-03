$env:Path += ";C:\Users\ThinkPad\.cargo\bin"
& "C:\Users\ThinkPad\OneDrive\Desktop\pocket.pal\backend\.venv\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel
& "C:\Users\ThinkPad\OneDrive\Desktop\pocket.pal\backend\.venv\Scripts\python.exe" -m pip install maturin
& "C:\Users\ThinkPad\OneDrive\Desktop\pocket.pal\backend\.venv\Scripts\python.exe" -m pip install --force-reinstall orjson pydantic-core
