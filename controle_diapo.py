import cv2 as cv
import numpy as np
from pynput.mouse import Button, Controller
from pynput import keyboard
import ctypes
from collections import deque
import time
import threading
import sys

user32 = ctypes.windll.user32

cam = cv.VideoCapture(0)

mouse_pos_x = 0
mouse_pos_y = 0

pts = deque(maxlen=32)
pts_direction = deque(maxlen=10)
counter = 0
(dX, dY) = (0, 0)
direction = ""

start = None
# chargement des classifiers
classifier_hand = cv.CascadeClassifier("main.xml")
classifier_palm = cv.CascadeClassifier("main_ferme.xml")

hand = True
#==========================


print("thread init...")
# listener sur le clavier
def keyboard_listener():
    print("listenr join")
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

def on_press(key):
    global hand
    print("key pressed: " + str(key))
    keypre = str(key)
    if keypre == "'h'":
        print("H key pressed")
        hand = True
    if keypre == "'j'":
        print("J key pressed")
        hand = False
#lancement du thread
kblistener_thread = threading.Thread(name='keyboard_listener', target=keyboard_listener)
kblistener_thread.daemon = True
kblistener_thread.start()


while cam.isOpened():
    ret, frame = cam.read()
    if not ret:
        continue
    frame_disp = frame.copy()

    # si la main est ouverte (clicker sur la touche H)
    if hand:
        hand = True
        # Controle de la sourie
        mouse = Controller()
        _keyboard = keyboard.Controller()
        try:
            _keyboard.release(keyboard.Key.ctrl)
            mouse.release(Button.left)
        except:
            pass
        # detection de la main
        clf = classifier_hand
        r_color = (0,255,0)
        d_rects = clf.detectMultiScale(frame, 1.3, 10)

        for (x, y, w, h) in d_rects:
            cv.rectangle(frame_disp, (x, y), (x+w, y+h), r_color)

            #calculation du centre de rectangle
            center_rec = (int(w/2)+x, int(h/2)+y)
            cv.circle(frame_disp, center_rec, 6, r_color,-1)
            # ajout du centre dans la liste des point
            pts.appendleft(center_rec)
            
            for i in np.arange(1, len(pts)) : 
                # si un point tracker est null ignore le
                if pts[i - 1] is None or pts[i] is None:
                    continue
                # verifier si en a assez des points dans la liste
                if counter >= 10 and i == 1 and len(pts) == 32:
                    # calculer la difference entre les points collecter
                    dX = pts[-10][0] - pts[i][0]
                    dirX = ""

                    if np.abs(dX) > 20:
                        # calculer la direction selon la valeur du dX
                        dirX = "East" if np.sign(dX) == 1 else "West"

                    direction = dirX

                    start = time.time()
                    cv.putText(frame_disp, dirX[::-1], (30, 30), cv.FONT_HERSHEY_SIMPLEX,0.65, (0, 255, 0), 3)

    # si la main est ferme (clicker sur la touche J)
    if not hand:
        hand = False
        # controle de la sourie est clavier
        mouse = Controller()
        _keyboard = keyboard.Controller()
        try:
            _keyboard.press(keyboard.Key.ctrl)
            mouse.press(Button.left)
        except:
            pass

        clf = classifier_palm
        r_color = (0,0,255)
        d_rects = clf.detectMultiScale(frame, 1.3, 10)

        for (x, y, w, h) in d_rects:
            cv.rectangle(frame_disp, (x, y), (x+w, y+h), r_color)
            #calculation du centre de rectangle
            center_rec = (int(w/2)+x, int(h/2)+y)
            cv.circle(frame_disp, center_rec, 6, r_color,-1)
            pts.appendleft(center_rec)

            #==================Mouse control====================
            mousepointX = mouse.position[0]
            mousepointY = mouse.position[1]
            # la resolution de l'ecran
            pantallaWidth = user32.GetSystemMetrics(0)
            pantallaHight = user32.GetSystemMetrics(1)
            # la resolution du fenetre
            cap_w = cam.get(cv.CAP_PROP_FRAME_WIDTH)
            cap_h = cam.get(cv.CAP_PROP_FRAME_HEIGHT)

            XScale = pantallaWidth / cap_w
            YScale = pantallaHight / cap_h
            
            OffsetX = (abs(cap_w - x) * XScale) - mousepointX
            OffsetY = (y * YScale) - mousepointY

            speedx = abs(OffsetX) * 0.8
            speedy = abs(OffsetY) * 0.8

            if OffsetX > 0 :
                mouse_pos_x = mouse_pos_x + speedx
            if OffsetX < 0 :
                mouse_pos_x = mouse_pos_x - speedx
            if OffsetY > 0 :
                mouse_pos_y = mouse_pos_y + speedy
            if OffsetY < 0 :
                mouse_pos_y = mouse_pos_y - speedy

            mouse.position = (mouse_pos_x, mouse_pos_y)
            #===============End========================
    #ajout de la direction au tableau
    pts_direction.appendleft(direction)

    _keyboard = keyboard.Controller()
    # si le nombre de direction WEST est superieur a 10
    if pts_direction.count("West") >= 10:
        # calculation du temps passe en movement
        done = time.time()
        elapsed = done - start
        if elapsed > 0.7 and elapsed < 1.3:
            print("==West==")
            _keyboard.press(keyboard.Key.left)
            _keyboard.release(keyboard.Key.left)
        pts_direction.clear()
    if pts_direction.count("East") >= 10:
        done = time.time()
        elapsed = done - start
        if elapsed > 0.7 and elapsed < 1.3:
            print("==East==")
            _keyboard.press(keyboard.Key.right)
            _keyboard.release(keyboard.Key.right)
        pts_direction.clear()   

    # retation horizontal de l'image 
    frame_flip = frame_disp.copy()
    frame_flip = cv.flip( frame_disp, 1)
    # afficher l'image
    cv.imshow("Hand Detection", frame_flip)
    counter += 1
    # presser la touche 'q' pour quiter
    keycv = cv.waitKey(1) & 0xFF
    if keycv == ord('q'):
        break
# ferme la fonetre
cv.destroyAllWindows()
cam.release()
sys.exit()
