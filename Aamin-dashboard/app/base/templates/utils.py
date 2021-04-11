import cv2


def gen(camera, type='normal_camera'):
    while True:
        if type == 'normal_camera':
            frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')