"""
tests/conftest.py
<<<<<<< HEAD
Shared pytest configuration and fixtures.
"""
import pytest
import requests

BASE = "http://localhost:8000"

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "ml: marks tests that require the ML model to be loaded"
    )

@pytest.fixture(scope="session", autouse=True)
def check_api_running():
    """Fail fast if the API is not running."""
    try:
        r = requests.get(f"{BASE}/", timeout=5)
        r.raise_for_status()
    except Exception:
        pytest.exit(
            "❌ API not reachable at http://localhost:8000\n"
            "   Run: docker compose up -d  before running tests",
            returncode=1
        )
=======
-----------------
Fixtures compartidos para todo el proyecto.
"""
import requests
import pytest

BASE = "http://localhost:8000"


def pytest_runtest_setup(item):
    """
    Antes de cada test que hace peticiones HTTP:
    verificar que el sistema esta accesible.
    No reseteamos scores (no hay endpoint para eso),
    pero si detectamos que el sistema esta bloqueando
    peticiones basicas lo indicamos claramente.
    """
    pass  # extensible si se necesita


@pytest.fixture(autouse=False)
def fresh_session():
    """Devuelve una sesion nueva con UA legitimo para cada test que lo pida."""
    s = requests.Session()
    s.headers.update({
        "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) pytest-fresh/1.0",
        "Accept-Language": "es-ES,es;q=0.9",
        "Accept-Encoding": "gzip, deflate",
    })
    return s
>>>>>>> a0911aa1f82906fcb977a3175a4e7549874f9073
