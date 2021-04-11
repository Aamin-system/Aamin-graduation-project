
import requests
from flask import Flask

app = Flask(__name__)

@app.route('/counter/<msg>',methods=["POST"])
def counter(msg):
    msg  = "hellloo it is me"
    requests.post('http://192.168.43.253:5004/count',json={'message': msg})
    return 'hello'



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5008)

