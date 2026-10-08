from importlib.metadata import PackageNotFoundError, version


try:
    __version__ = version("skydance")
except PackageNotFoundError:
    __version__ = "(local)"
