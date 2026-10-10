"""PDF Escolar: selección y combinación local de páginas PDF."""

try:
    from ._build_version import __version__ as __version__
except ImportError:
    # El archivo se genera durante la compilación de instaladores.
    __version__ = "0.1.0"
