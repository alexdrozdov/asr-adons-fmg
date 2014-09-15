import os
import sys

__all__ = []
print "Extending search path to", os.path.dirname(__file__)
sys.path.append(os.path.dirname(__file__))
