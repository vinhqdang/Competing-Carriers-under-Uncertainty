"""Shared settings for the TRIP package scripts."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))      # mfg/submission/trip  (the package folder)
SUB = os.path.dirname(HERE)                            # mfg/submission
MFG = os.path.dirname(SUB)                             # mfg
ZENODO_DOI = None   # set to e.g. '10.5281/zenodo.1234567' after the deposit; used by make_docs.py (title page, data statement)
GITHUB = 'https://github.com/vinhqdang/Competing-Carriers-under-Uncertainty'
