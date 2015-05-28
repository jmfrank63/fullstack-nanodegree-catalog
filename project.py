
# A very simple Flask Hello World app for you to get started with...

from flask import Flask

app = Flask(__name__)

#@app.route('/')
@app.route('/hello')
def hello_world():
    return 'Hello World!'

if __name__ == '__main__':
    app.debug = True
    app.run(host = '0.0.0.0', port = 8080)

