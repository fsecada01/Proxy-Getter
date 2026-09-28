"""Tests for how proxy_getter.consts picks the database path."""

import importlib
import sys
from pathlib import Path

import pytest

import proxy_getter

HOST_MODULES = ("backend", "backend.settings", "backend.settings.consts")


def _write_host(root: Path, consts_source: str) -> Path:
    """Create a real ``backend.settings.consts`` package under ``root``."""
    settings = root / "backend" / "settings"
    settings.mkdir(parents=True)
    (root / "backend" / "__init__.py").write_text("")
    (settings / "__init__.py").write_text("")
    (settings / "consts.py").write_text(consts_source)
    return root


@pytest.fixture
def load_consts(monkeypatch):
    """Re-import proxy_getter.consts under a given env and host app.

    monkeypatch restores sys.modules, sys.path and the package's
    ``consts`` attribute afterwards, so no test sees another's module.
    """

    def load(env=None, host_root=None):
        monkeypatch.delenv("PROXY_DB_PATH", raising=False)
        if env is not None:
            monkeypatch.setenv("PROXY_DB_PATH", env)
        for name in (*HOST_MODULES, "proxy_getter.consts"):
            monkeypatch.delitem(sys.modules, name, raising=False)
        monkeypatch.delattr(proxy_getter, "consts", raising=False)
        if host_root is not None:
            monkeypatch.syspath_prepend(str(host_root))
        importlib.invalidate_caches()
        return importlib.import_module("proxy_getter.consts")

    return load


def test_host_str_base_dir(load_consts, tmp_path):
    # both known hosts define BASE_DIR as a str
    base = tmp_path / "app"
    host = _write_host(tmp_path / "host", f"BASE_DIR = {str(base)!r}\n")

    consts = load_consts(host_root=host)

    assert consts.DB_PATH == base.resolve() / "proxy_urls.db"


def test_host_path_base_dir(load_consts, tmp_path):
    base = tmp_path / "app"
    host = _write_host(
        tmp_path / "host",
        f"from pathlib import Path\nBASE_DIR = Path({str(base)!r})\n",
    )

    consts = load_consts(host_root=host)

    assert consts.DB_PATH == base.resolve() / "proxy_urls.db"


def test_no_host_uses_package_dir(load_consts):
    consts = load_consts()

    assert consts.DB_PATH == Path(consts.__file__).parent.resolve() / (
        "proxy_urls.db"
    )


def test_env_wins_and_skips_host_settings(load_consts, tmp_path):
    # e.g. leads_ai without SECRET_KEY: its settings raise on import
    host = _write_host(tmp_path / "host", "raise RuntimeError('no key')\n")
    db = tmp_path / "db" / "proxies.db"

    consts = load_consts(env=str(db), host_root=host)

    assert consts.DB_PATH == db.resolve()
    assert consts.sqlite_address == f"sqlite:///{db.resolve()}"


def test_failing_host_settings_propagate_without_env(load_consts, tmp_path):
    host = _write_host(tmp_path / "host", "raise RuntimeError('no key')\n")

    with pytest.raises(RuntimeError, match="no key"):
        load_consts(host_root=host)


def test_host_missing_dependency_is_not_treated_as_no_host(
    load_consts, tmp_path
):
    # must not silently fall back to the package directory
    host = _write_host(tmp_path / "host", "import not_installed_dep\n")

    with pytest.raises(ModuleNotFoundError, match="not_installed_dep"):
        load_consts(host_root=host)


def test_env_relative_and_home(load_consts, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert load_consts(env="rel/p.db").DB_PATH == tmp_path.resolve() / (
        "rel/p.db"
    )

    home = load_consts(env="~/p.db").DB_PATH
    assert home == (Path.home() / "p.db").resolve()


def test_base_dir_is_deprecated_but_available(load_consts):
    consts = load_consts()

    with pytest.warns(DeprecationWarning, match="DB_PATH"):
        base_dir = consts.BASE_DIR

    assert base_dir == consts.DB_PATH.parent
