import os
from dotenv import load_dotenv

# This loads all variables from .env file
load_dotenv()

DATA_BASE_DIR = os.environ.get('DATA_BASE_DIR')

if not DATA_BASE_DIR:
    print("Warning: DATA_BASE_DIR not set in .env file")
    DATA_BASE_DIR = './data'  # Fallback to relative path