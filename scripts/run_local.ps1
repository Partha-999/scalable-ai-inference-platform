Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

.\.venv\Scripts\Activate.ps1
python -m scripts.start_ray_serve
