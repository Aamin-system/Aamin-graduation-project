# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 18:57:44 2019

@author: seraj
"""

import time
from datetime import datetime
import cv2 
from flask import Flask, render_template, Response
import numpy as np
import threading
from math import sqrt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import mapper, sessionmaker
from imutils.video import VideoStream
import requests
app = Flask(__name__)



class sds(object):
    pass

def loadSession():
    """"""    
  
    engine = create_engine('mysql+pymysql://root:''@192.168.8.106:3308/sds', echo=True)
    
    metadata = MetaData(engine)

    metadata.reflect(bind=engine)
    conn = engine.connect()
    
    violations = Table('violations', metadata, autoload=True)
    mapper(sds, violations)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    return session,conn,violations





session,conn,violations = loadSession()




@app.route('/')
def index():
    """Video streaming home page."""
    #requests.post("http://192.168.8.106:5009/noti")

    return render_template('index.html')


@app.route('/send_message/<msg>',methods=["POST"])
def send_message(msg):
    requests.post('http://192.168.8.106:5009/noti', json={'message': msg})
    print("gjhghghghghhhgghgfghgh")
    return "sent:"

        
def violation(frame):
    cv2.imwrite('violation'+str(violation.counter)+'.jpeg',frame)
    
    now = datetime.now()
    viol_date = now.strftime("%d/%m/%Y")
    
    viol_time = now.strftime("%H:%M:%S")
    #print(type(viol_time))
    print("viol time =", viol_time)
    print("count = ", violation.counter)
    meg = "new violation"
    send_message(meg)
    stor_in_DB(int(violation.counter),'distance',viol_date,viol_time)
    
    violation.counter+=1

violation.counter=session.query(sds).count()+1
   
   
def stor_in_DB(id,type,date,time):

    with open('violation'+str(id)+'.jpeg',"rb") as f:
        binary_img = f.read()
        
    print("yessssssssssssssssssssssssssssssssssssssssss")
      

    

    conn.execute(violations.insert(), {"ID": id,"Type": type,"Date": date,"Time": time, "Image": binary_img })
    
   

          
@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    
    def gen():
        lock = True 
        neural_network = cv2.dnn.readNetFromCaffe("SSD_MobileNet_prototxt.txt", "SSD_MobileNet.caffemodel")
        cap = cv2.VideoCapture(0)
        #
        
        confidence_factor = float(0.2)

        label = "person"


        # Load model
        print("\nLoading model...\n")
        
        print("\nStreaming video using device...\n")


        # Capture video from camera

        


        while True:   

            # Capture one frame after another
            ret, frame = cap.read()

            if not ret:
                print("no camera")
                break
            
            frame = cv2.flip(frame, 1)

            # h ->> hight , w ->> width
            (h, w) = frame.shape[:2]

            # cv2.dnn.blobFromImage(image, scalefactor=1.0, size, mean)
            # Resize the frame to suite the model requirements. Resize the frame to 300X300 pixels
            blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (299, 299), 127.5)

            neural_network.setInput(blob)
            # 4D numpy array:it is basically a matrix of matrices
            detections =  neural_network.forward()



            position_dict = dict()
            coordinates = dict()

            # Focal_length
            Focal_length = 55

            # shape[2] = 100 >> detections.shape(1, 1, 100, 7)
            #parameter(.no row,.no column, Rows in a matrix ,  columns in a matrix)
            # .no row * .no column = .no matrices 
            # column 1 has the object id 
            # column 2 has the confidence
            for i in range(detections.shape[2]):

                # return number between 0-1
                confidence = detections[0, 0, i, 2]

                if confidence > confidence_factor:

                    # Filtering only persons detected in the frame. Class Id of 'person' is 15
                    person =  int(detections[0, 0, i, 1])
                        
                    #detections[0, 0, i, 3:7] = [0. 0. 0. 0.]
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                
                    #(startX, startY, endX, endY) = [.no, .no, .no, .no]
                    (startX, startY, endX, endY) = box.astype('int')
                    
                    
                    if person == 15:

                        # Draw bounding box around the person
                        cv2.rectangle(frame, (startX, startY), (endX, endY), (0,255,0), 2)

                        coordinates[i] = (startX, startY, endX, endY)

                        # center point of bounding box
                        x_mid = round((startX+endX)/2,4)
                        y_mid = round((startY+endY)/2,4)

                        image_height = round(endY-startY,4)
                        #print(image_height)
                        """ 
                        Distance from camera based on triangle similarity: D = H*F/h
                        where:

                        D = distance from lens to object
                        H = Real height of object
                        F = focal length
                        h = height of object's image 

                        """  
                        distance = (165 * Focal_length)/image_height
                        #print("Distance(cm):{dist}\n".format(dist=distance))
                        # I stopped here
                        # Mid-point of bounding boxes (in cm) based on triangle similarity technique
                        x_mid_cm = (x_mid * distance) / Focal_length
                        y_mid_cm = (y_mid * distance) / Focal_length
                        position_dict[i] = (x_mid_cm,y_mid_cm,distance)
                        #print(position_dict)

            # Distance between every object detected in a frame
            close_objects = set()
            for i in position_dict.keys():
                for j in position_dict.keys():
                    if i < j:
                        #sqrt(pow(0x_mid_cm-1x_mid_cm,2)+pow(0y_mid_cm-1y_mid_cm,2)+pow(0distance-1distance,2))
                        dist = sqrt(pow(position_dict[i][0]-position_dict[j][0],2) + pow(position_dict[i][1]-position_dict[j][1],2) + pow(position_dict[i][2]-position_dict[j][2],2))/2

                        # Check if distance less than 2 metres or 200 centimetres
                        if dist < 200:
                            close_objects.add(i)
                            close_objects.add(j)
            COLOR = (0,0,0)
            for i in position_dict.keys():
                if i in close_objects:
                    COLOR = (0,0,255) #red
                    
                else:
                    COLOR = (0,255,0) #green
                    
                (startX, startY, endX, endY) = coordinates[i]
                cv2.rectangle(frame, (startX, startY), (endX, endY), COLOR, 2)
                y = startY - 15 if startY - 15 > 15 else startY + 15
                # Convert cms to feet
                cv2.putText(frame, 'Depth: {i} ft'.format(i=round(position_dict[i][2]/30.48,4)), (startX, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR, 2)
                
                
                
            if COLOR ==(0,0,255):
               if lock:
                    start_time = threading.Timer(3,violation,[frame])
                    lock = False
                    start_time.start()
                    #print(threading.active_count())
            elif COLOR == (0,255,0) and lock== False:
                    lock=True
                    start_time.cancel()


            frame = cv2.imencode('.jpeg', frame)[1].tobytes()
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
            key = cv2.waitKey(1)
            if key == 27:
                break
    
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':

    app.run(host='0.0.0.0',port='5005')


