import os
import secrets
from flask import render_template, url_for, flash, redirect, request, abort
from flaskDemo import app

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/')
def home():
    return render_template('home.html')
