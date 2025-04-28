import os
import sys

# Set the working directory to the temporary extraction path
if hasattr(sys, '_MEIPASS'):
    os.chdir(sys._MEIPASS)