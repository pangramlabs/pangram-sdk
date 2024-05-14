"""Defile all variables to be accessible from `import pangram`."""
__version__ = "0.1.0"
__author__ = "Max Spero"
__email__ = "max@pangramlabs.com"
__license__ = "MIT"

from pangram.text_classifier import PangramText

__all__ = ["text_classifier", "PangramText"]
