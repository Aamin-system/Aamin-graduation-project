from django.conf.urls import url
import json
from flask import Flask,jsonify,request
@app.route("/_data")
def chartData():
    data = {
        "values" : 24,
    } 
    return jsonify(data)
