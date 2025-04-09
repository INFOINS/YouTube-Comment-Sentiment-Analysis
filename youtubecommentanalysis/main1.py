from flask import Flask, render_template, request, redirect, url_for
app=Flask(__name__)
@app.route('/')
def hellO():
  return render_template('index.html')

@app.route('/login')