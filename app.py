from flask import Flask, request
from flask import render_template, flash

app = Flask(__name__)
app.app_context().push()

@app.route('/')
def index():
    return render_template('index.html')