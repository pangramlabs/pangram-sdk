"""Defile all variables to be accessible from `import pangram`."""
__version__ = "0.3.0"
__author__ = "Max Spero"
__email__ = "max@pangram.com"
__license__ = "MIT"

from pangram.text_classifier import PangramText
Pangram = PangramText

__all__ = ["PangramText", "Pangram"]
