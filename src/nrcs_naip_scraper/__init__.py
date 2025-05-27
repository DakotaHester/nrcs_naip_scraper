"""
NRCS NAIP Scraper Package

A Python package for downloading NAIP (National Agriculture Imagery Program) 
data from the NRCS Box folder.
"""

from .scraper import NAIPScraper

__version__ = "0.1.0"
__author__ = "Dakota Hester <dh2306@msstate.edu>>"

__all__ = [
    "NAIPScraper",
]