import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import pytesseract and monkey-patch it before importing the robot scripts
import pytesseract.pytesseract

pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# Now import the robot scripts
import BTS.BTS_Mobile

print("Successfully imported BTS_Mobile")
