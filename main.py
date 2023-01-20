# import packages
import cv2
import os
import pickle
import json
from datetime import datetime
import numpy as np
import face_recognition
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import pyttsx3 as textspeech  # pyttsx3 is also working offline

engine = textspeech.init()  # obj creation
# firebase url's
cred = credentials.Certificate("Serviceaccount.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://my-attendance-system-in-opencv-default-rtdb.firebaseio.com/",
    'storageBucket': "my-attendance-system-in-opencv.appspot.com"
})
# access cam
capt = cv2.VideoCapture(0)
# capt = cv2.VideoCapture(0)
capt.set(3, 640)  # width
capt.set(4, 480)  # height

# import images
imgpath = 'C:/Users/arunk/PycharmProjects/Face_attendance_system/Resource/Particulates'
pathlist = os.listdir(imgpath)  # retrieves a list of all files and directories in a given directory
# print(pathlist)
imglist = []
student_name = []
for path in pathlist:
    imglist.append(cv2.imread(os.path.join(imgpath, path)))
    student_name.append(os.path.splitext(path)[0])
# print(len(imglist))
print(student_name)

# Loading the encoded values
print("Loading encode files...")
e_file = open("Encoded_values.p", "rb")
encodelistknown = pickle.load(e_file)
e_file.close()
encodelist, student_name = encodelistknown
# print(student_name)
print("Encoded file loaded")

# webcam Background
imgBackground = cv2.imread('C:/Users/arunk/PycharmProjects/Face_attendance_system/Resource/Background cover.png')
cv2.startWindowThread()  # threading -  show the window and have the program continue execution

# Begin to detect the face detection in each frame
modetype = 0
counter = 0
id = -1

while True:
    success, img = capt.read()

    # before face recognize,to compress our image size in smaller for reduce computation power
    # sacle it on 1/4th of sizes so values is 0.25
    small_img = cv2.resize(img, (0, 0), None, 0.25,
                           0.25)  # resize(source_file,dsize,distance,fx,fy)  fx,fy is scale size
    # convert color format   it will properly work it
    small_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # needed to faces and encoded values in current frame
    face_currentfrm = face_recognition.face_locations(small_img)
    encode_currentfrm = face_recognition.face_encodings(small_img, face_currentfrm)

    # loop through all the  also using zip method in multiple method in same tym
    for encodeface, facelocation in zip(encode_currentfrm, face_currentfrm):
        matches = face_recognition.compare_faces(encodelist, encodeface,
                                                 tolerance=0.6)  # compare currents face,tolerance: How much distance between faces to consider it a match. Lower is more strict. 0.6 is typical best performance.
        faceDis = face_recognition.face_distance(encodelist, encodeface)  # face distance for better match

        imgBackground[195:195 + 480,
        73:73 + 640] = img  # split the left-side box to fix it   startimg point of height and width
        imgBackground[63:63 + 507, 778:778 + 414] = imglist[modetype]  # 63:63,778:778

        matchIndex = np.argmin(faceDis)
        if matches[matchIndex]:
            # print("Our Student")
            # print(student_name[matchIndex])
            # else:
            # print("Unknown person")

            y1, x2, y2, x1 = facelocation
            y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
            bound_box = 73 + x1, 195 + y1, x2 - x1, y2 - y1
            imgBackground = cv2.rectangle(imgBackground, bound_box, (0, 255, 0), 2)

            id = student_name[matchIndex]
            print(id)
            if counter == 0:
                counter = 1
                modetype = 1

            if counter != 0:
                if counter == 1:
                    student_details = db.reference(f'Student_Info/{id}').get()
                    print(student_details)

                    # Update data into database
                    dt_obj = datetime.strptime(student_details['Attendance_time'], "%Y-%m-%d %H:%M:%S")
                    time_elapse = (datetime.now() - dt_obj).total_seconds()  # total_seconds() is time delta
                    print(time_elapse)

                    # Set the time limit to take data
                    if time_elapse > 3600:  # set 1hour
                        ref = db.reference(f'Student_Info/{id}')
                        # ref.child('Attendance_time').set(student_details['Attendance_time'])
                        ref.child('Attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


                        # save student data in csv file
                        def Mark_att_csv(name):
                            with open('today_attendance.csv', 'r+') as f:
                                datalist = f.readlines()
                                namelist = []
                                for line in datalist:
                                    entry = line.split(',')
                                    namelist.append(entry[0])

                                if name not in datalist:
                                    now = datetime.now()
                                    time_str = now.strftime("%H:%M:%S")
                                    f.writelines(f'\n{name},{time_str}')
                                    print(Mark_att_csv(name))

                                    # setting up text to speech converter
                                    """volume"""
                                    volume = engine.getProperty('volume')
                                    print(volume)
                                    engine.setProperty('volume', 1.0)  # min=0,max=1
                                    """voice"""
                                    voices = engine.getProperty('voices')
                                    engine.setProperty('voice', voices[1].id)  # changing index,changes voices 1 for female ,0 for male

                                    statement = str("Welcome Back" + name)
                                    engine.say(statement)
                                    engine.runAndWait()
                                    engine.stop()





                    # convert string format into current time
                    def myconverter(Attendance_time):
                        if isinstance(Attendance_time, datetime.datetime.now()):
                            return Attendance_time.__str__()
                        print(json.dumps(student_details, default=myconverter))


                    student_details['Attendance_time'] = datetime.now()
                    # print("Successfully added")

    # cv2.imshow("face",img)
    cv2.imshow("Face Attendance System", imgBackground)
    # cv2.imshow("Face Attendance System", imgBackground)
    cv2.waitKey(1)
