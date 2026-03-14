"""Seed inicial del repositorio.

Notas para desarrolladores y agentes GPT:
- Este seed es deliberadamente pequeño para el paso 2.
- En el paso 11 debe evolucionar a `make bootstrap-test-state` con fixtures completos.
"""

import json
from pathlib import Path

seed_data = {
    "company": {"name": "Demo ERP Barrio", "rut": "76.123.456-7"},
    "branch": {"name": "Casa Matriz", "code": "BR-001"},
    "users": [
        {"email": "admin@example.com", "role": "admin"},
        {"email": "cajero@example.com", "role": "cajero"},
    ],
}

output_path = Path("infra/seeds/dev_seed.json")
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(json.dumps(seed_data, indent=2), encoding="utf-8")

print(f"Seed generado en {output_path}")
