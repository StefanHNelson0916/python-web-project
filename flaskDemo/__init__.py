from flask import Flask
from logging import FileHandler,WARNING

app = Flask(__name__)

file_handler = FileHandler('errorlog.txt')
file_handler.setLevel(WARNING)

from flaskDemo import routes
