import os

import toml
import yaml
from fastapi.openapi.utils import get_openapi

from src.main import app

OUTPUT_DIR = "outputs"

if __name__ == "__main__":
    with open("pyproject.toml", "r") as fd:
        poetry_info = toml.load(fd)["tool"]["poetry"]
        version = poetry_info["version"]
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(f"{OUTPUT_DIR}/openapi.yaml", "w") as fd:
        openapi = get_openapi(
            title="Backend APIs",
            version=version,
            description="Backend APIs",
            contact={
                "name": "ABEJA Inc",
                "url": "https://www.abejainc.com",
                "email": "info@abejainc.com",
            },
            servers=[{"url": "https://api.example.com"}],
            routes=app.routes,
        )
        yaml.dump(openapi, fd, sort_keys=False, encoding="utf-8", allow_unicode=True)
