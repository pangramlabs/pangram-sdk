"""Defile all variables to be accessible from `import pangram`."""
__version__ = "0.1.8"
__author__ = "Max Spero"
__email__ = "max@pangramlabs.com"
__license__ = "MIT"

from pangram.text_classifier import PangramText
Pangram = PangramText

__all__ = ["PangramText", "Pangram"]
