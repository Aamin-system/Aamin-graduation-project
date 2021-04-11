import time
from datetime import datetime
import cv2 
from flask import Flask, render_template, Response
import numpy as np
import threading
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import mapper, sessionmaker
import requests


app = Flask(__name__)



@app.route('/')
def index():
    return render_template('index.html')


class sds(object):
    pass

def loadSession():
    """"""    
    # to conncet with mysql that run on raperry pi :
    # engine = create_engine('mysql://root:pass@192.168.1.10:3306/sds', echo=True) 
    engine = create_engine('mysql+pymysql://root:''@192.168.1.6:3308/sds', echo=False)
    
    metadata = MetaData(engine)

    metadata.reflect(bind=engine)
    conn = engine.connect()

    violations = Table('violations', metadata, autoload=True)
    mapper(sds, violations)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    return session,conn,violations


session,conn,violations = loadSession()


def raw_to_8bit(data):
  cv2.normalize(data, data, 0, 65535, cv2.NORM_MINMAX)
  np.right_shift(data, 8, data)
  return cv2.cvtColor(np.uint8(data), cv2.COLOR_GRAY2RGB)

def get_temperature(temperatures, bbox):
    # Consider the raw temperatures insides the face bounding box.
    left = int(bbox[0])
    top = int(bbox[1])
    right = int(bbox[2])
    bottom = int(bbox[3])
    crop = temperatures[top:bottom, left:right]
    if crop.size == 0:
        return 0
    # Use the maximum temperature across the face.
    # The raw temperature is in centikelvin.
    max_temp = np.max(crop)
    
    
    return max_temp / 100 - 273.15







@app.route('/video_feed')
def video_feed():
    def Temperature():
        
        thermal = cv2.VideoCapture(0 + cv2.CAP_V4L2)
        thermal.set(3,160)
        thermal.set(4,120)
        thermal.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"Y16 "))
        thermal.set(cv2.CAP_PROP_CONVERT_RGB, 0)
        
        net = cv2.dnn.readNetFromCaffe('deploy.prototxt.txt', 'ssd_iter_140000.caffemodel')
        while True:
            # Capture video or webcam
            ret , frame = thermal.read()
            img = frame.copy()
        
            if not ret:
                thermal.release()
                print("No thermal ")
                break
            
            frame = raw_to_8bit(frame)
            
            
            (h, w) = frame.shape[:2]
            blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0,
                (300, 300), (104.0, 177.0, 123.0))

            net.setInput(blob)
            detections = net.forward()

            # loop over the faces detections
            for i in range(0, detections.shape[2]):
                confidence = detections[0, 0, i, 2]

                # filter out weak detections by ensuring the `confidence` is correct
                if confidence > 0.3:
                    
                 
                    # compute the (x, y)-coordinates of the bounding box for the faces
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    (startX, startY, endX, endY) = box.astype("int")
            
                    bbox = (startX, startY, endX, endY)
                    temperature = get_temperature(img,bbox)
                    y = startY - 10 if startY - 10 > 10 else startY + 10
                    
                    #temp1 = get_temperature(raw_buffer,bbox)
                    cv2.rectangle(frame, (startX, startY), (endX, endY),
                        (255,255,255), 1)
                    
                   
                    cv2.putText(frame,"{i} ".format( i = str(int(temperature))), (startX, y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255,255,255), 1)

            

            frame = cv2.resize(frame, (300,300))

            frame = cv2.imencode('.jpeg', frame)[1].tobytes()
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
            key = cv2.waitKey(1)
            if key == 27:
                thermal.release()
                break
    
    return Response(Temperature(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0',port='5004')

cv2.destroyAllWindows()
thermal.release()
