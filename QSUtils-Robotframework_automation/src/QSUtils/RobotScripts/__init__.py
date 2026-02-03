# RobotScripts package
import sys
import os

# Add the BTS directory to the Python path so that the relative imports work
bts_path = os.path.join(os.path.dirname(__file__), "BTS")
if bts_path not in sys.path:
    sys.path.insert(0, bts_path)
