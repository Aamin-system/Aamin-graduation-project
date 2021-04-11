import numpy as np 
import cv2




def Intersection(id,y):

   if id not in Intersection.In: 
      if y >= 220 and y <= 250:
         print("increment: ",id)
         Intersection.counter+=1
         Intersection.In.append(id)

   if id not in Intersection.out and Intersection.counter!=0:
      if y <= 280 and y >= 250:
         print("decremnt: ",id)
         Intersection.counter-=1
         Intersection.out.append(id)
   
   if id in Intersection.out and id in Intersection.In:
      Intersection.In.remove(id)
      Intersection.out.remove(id)
   
   
         
def drawBox(id,img, bbox):
    x_mid = int(round((bbox[0]+bbox[2])/2,4))
    y_mid = int(round((bbox[1]+bbox[3])/2,4))

    rectagleCenterPont = (x_mid, y_mid-50)
    x,y,w,h = int(bbox[0]),int(bbox[1]),int(bbox[2]),int(bbox[3])
    cv2.circle(frame, rectagleCenterPont, 3, (0, 0, 255), 5)
    cv2.putText(frame, "id{}".format(str(id)), (x_mid+10, y_mid),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
      
      



Intersection.In = []
Intersection.out = []
id = 0
confidence_factor = float(0.9)
Intersection.counter = 0
frame_number = 0
trackableObjects = {}

count = int(0)
tracker = dict()
#tracker = cv2.TrackerMOSSE_create() #faster but not accurte
#tracker = cv2.TrackerCSRT_create()#slower but more accurte 


# Load model
neural_network = cv2.dnn.readNetFromCaffe("SSD_MobileNet_prototxt.txt", "SSD_MobileNet.caffemodel")

print("\nStreaming...\n")

# Capture video from camera
cap = cv2.VideoCapture(0)

while cap.isOpened():

    # Capture one frame after another
    ret, frame = cap.read()
    frame1 = frame.copy()
    
    if not ret:
        break

    # h ->> height  , w ->> width
    (h, w) = frame.shape[:2]

    blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)

    neural_network.setInput(blob)

    detections =  neural_network.forward()

    
    cv2.resize(frame, (300, 300))
    cv2.line(frame, (0, 220), (700, 220), (0, 255, 0), 2)
    cv2.line(frame, (0, 250), (700, 250), (255,255,0), 2)
    cv2.line(frame, (0, 280), (700, 280), (255, 0, 255), 2)
    cv2.putText(frame, "count: {}".format(str(Intersection.counter)), (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    for i in range(detections.shape[2]):

        

        # return number between 0-1
        confidence = detections[0, 0, i, 2]

        if confidence > confidence_factor:

            frame_number+=1
            #print(frame_number)
            

            # Filtering only persons detected in the frame. Class Id of 'person' is 15
            person =  int(detections[0, 0, i, 1])

            if person == 15:

                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
           
                (startX, startY, endX, endY) = box.astype('int')
                bbox = (startX, startY, endX, endY)
                #cv2.rectangle(frame, (startX, startY), (endX, endY), (0,255,0), 2)
                #cv2.TrackerMOSSE_create()
                tracker[i]= cv2.TrackerCSRT_create() 
                tracker[i].init(frame, bbox)
                y_mid = int(round((startY+endY)/2,4))
                Intersection(i,y_mid-70)
                #print(len(tracker))
            

          
            

                # Draw bounding box around the person
                #cv2.rectangle(frame, (startX, startY), (endX, endY), (0,255,0), 2)
    for i in tracker.keys():
        #print(type(tracker[i]))
        success, bbox = tracker[i].update(frame)
        if success:
            drawBox(i,frame, bbox)
        else:
            cv2.putText(frame, "lost", (75, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)



    cv2.namedWindow('Frame',cv2.WINDOW_NORMAL)
    # Show frame

    #print(tracker.getclass())
    cv2.imshow('Frame', frame)
    
    key = cv2.waitKey(1) & 0xFF
    # Press `q` to exit
    if key == ord("q"):
        break
    


# Clean
cap.release()
cv2.destroyAllWindows()


if __name__ == '__main__':
    
    app.run(port=5005)