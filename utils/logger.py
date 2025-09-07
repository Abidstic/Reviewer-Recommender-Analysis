import logging
import os

FOLDER_PATH = 'logs'

if not os.path.exists(FOLDER_PATH):
    os.makedirs(FOLDER_PATH)

logging.basicConfig(
    filename=f'{FOLDER_PATH}/{len(os.listdir(FOLDER_PATH)) + 1}.info.log',
    filemode='w',
    format='pid=%(process)d - %(asctime)s - %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

info_logger = logging.getLogger(__name__)
