"""PDF Escolar: selección y combinación local de páginas PDF."""

try:
    from ._build_version import __version__ as __version__
except ImportError:
    # El archivo se genera durante la compilación de instaladores.
    __version__ = "0.1.0"

try:
    from ._build_version import __build_commit__ as __build_commit__
    from ._build_version import __build_run_url__ as __build_run_url__
except ImportError:
    # Builds del código fuente no provienen necesariamente de GitHub Actions.
    __build_commit__ = "local"
    __build_run_url__ = ""
