from flask import Flask

app = Flask(__name__)

@app.route('/message', methods=['GET'])
def get_message():
    return "not implemented yet"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
