import pytesseract
import os
import sys

# Set the correct path for Tesseract
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# Also set the environment variable for Tesseract
os.environ["TESSERACT_CMD"] = "/usr/bin/tesseract"

# If running in a virtual environment, also set the path there
if hasattr(sys, "real_prefix") or (
    hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
):
    # We are in a virtual environment
    # Set the Tesseract path for the virtual environment
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
