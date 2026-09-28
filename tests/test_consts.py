"""Tests for how proxy_getter.consts picks the database path."""

import importlib
import sys
import types
from pathlib import Path

import pytest

HOST_MODULES = ("backend", "backend.settings", "backend.settings.consts")


class _BrokenSettings(types.ModuleType):
    """A host settings module whose import-time validation fails."""

    def __getattr__(self, name):
        raise RuntimeError("SECRET_KEY missing")


@pytest.fixture
def load_consts(monkeypatch):
    """Re-import proxy_getter.consts under a given env and host app."""

    def load(env=None, host=None):
        monkeypatch.delenv("PROXY_DB_PATH", raising=False)
        if env is not None:
            monkeypatch.setenv("PROXY_DB_PATH", env)
        for name in (*HOST_MODULES, "proxy_getter.consts"):
            monkeypatch.delitem(sys.modules, name, raising=False)
        if host is not None:
            for name in HOST_MODULES[:-1]:
                package = types.ModuleType(name)
                package.__path__ = []
                monkeypatch.setitem(sys.modules, name, package)
            monkeypatch.setitem(sys.modules, HOST_MODULES[-1], host)
        return importlib.import_module("proxy_getter.consts")

    return load


def _host(base_dir):
    module = types.ModuleType(HOST_MODULES[-1])
    module.BASE_DIR = base_dir
    return module


def test_host_str_base_dir(load_consts, tmp_path):
    # both known hosts define BASE_DIR as a str
    consts = load_consts(host=_host(str(tmp_path)))

    assert consts.DB_PATH == tmp_path.resolve() / "proxy_urls.db"


def test_host_path_base_dir(load_consts, tmp_path):
    consts = load_consts(host=_host(tmp_path))

    assert consts.DB_PATH == tmp_path.resolve() / "proxy_urls.db"


def test_no_host_uses_package_dir(load_consts):
    consts = load_consts()

    assert consts.DB_PATH == Path(consts.__file__).parent.resolve() / (
        "proxy_urls.db"
    )


def test_env_wins_and_skips_host_settings(load_consts, tmp_path):
    db = tmp_path / "db" / "proxies.db"

    consts = load_consts(env=str(db), host=_BrokenSettings("broken"))

    assert consts.DB_PATH == db.resolve()
    assert consts.sqlite_address == f"sqlite:///{db.resolve()}"


def test_env_relative_and_home(load_consts, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert load_consts(env="rel/p.db").DB_PATH == tmp_path.resolve() / (
        "rel/p.db"
    )

    home = load_consts(env="~/p.db").DB_PATH
    assert home == (Path.home() / "p.db").resolve()
