# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import os,shutil
from flask import jsonify, render_template, redirect, request, url_for, Response, flash
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user
)
from datetime import datetime,date
from app import db, login_manager
from app.base import blueprint
from app.base.forms import LoginForm, CreateAccountForm
from app.base.models import User,violations
from app.base.util import verify_pass
from app.base import MysqlDB
import base64
import json
import calendar
import pyautogui
import cv2
@blueprint.route('/')
def route_default():
    return redirect(url_for('base_blueprint.login'))

## Login & Registration

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)
    if 'login' in request.form:
        
        # read form data
        username = request.form['username']
        password = request.form['password']

        # Locate user
        user = User.query.filter_by(username=username).first()
        
        # Check the password
        if user and verify_pass( password, user.password):

            login_user(user)
            return redirect(url_for('base_blueprint.route_default'))

        # Something (user or pass) is not ok
        return render_template( 'accounts/login.html', msg='Wrong user or password', form=login_form)

    if not current_user.is_authenticated:
        return render_template( 'accounts/login.html',
                                form=login_form)
    return redirect(url_for('home_blueprint.index'))

@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    login_form = LoginForm(request.form)
    create_account_form = CreateAccountForm(request.form)
    if 'register' in request.form:

        username  = request.form['username']
        email     = request.form['email'   ]

        # Check usename exists
        user = User.query.filter_by(username=username).first()
        if user:
            return render_template( 'accounts/register.html', 
                                    msg='Username already registered',
                                    success=False,
                                    form=create_account_form)

        # Check email exists
        user = User.query.filter_by(email=email).first()
        if user:
            return render_template( 'accounts/register.html', 
                                    msg='Email already registered', 
                                    success=False,
                                    form=create_account_form)

        # else we can create the user
        user = User(**request.form)
        db.session.add(user)
        db.session.commit()

        return render_template( 'accounts/register.html', 
                                msg='User created please <a href="/login">login</a>', 
                                success=True,
                                form=create_account_form)

    else:
        return render_template( 'accounts/register.html', form=create_account_form)

@blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('base_blueprint.login'))

@blueprint.route('/shutdown')
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'

## Errors

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('page-403.html'), 403

@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('page-403.html'), 403

@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('page-404.html'), 404

@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('page-500.html'), 500


## if Violation detected this route is used to insert the violation data into the database  
# Also genarate the notifaction by using Note='True'
# @blueprint.route("/mysqltest")
# def mysqltest():
#     print("i'm is mysqldatabes ")
    
#     #return redirect(url_for('index'))
    
#     return render_template("index.html",Note="True")


@blueprint.route("/mysqltest",methods=['GET', 'POST'])
def sqltest():
    count = 0
    data = MysqlDB.get_all()
    for i in data:
        count=count+1

    print('old_current: ',count)

    MysqlDB.Violation_detected("occupancy")
    rows = MysqlDB.get_No_of_rows()
    print('New_current: ',rows)


    return render_template("index.html")

#

@blueprint.route("/search_by_type",methods=['GET', 'POST'])
def search_by_type():
    search_term = request.form.get('search_term').lower()
    data = MysqlDB.get_Type(search_term)
    imgs=[]
    for i in data:
        imgs.append(base64.b64encode(i["Image"]).decode('utf-8'))

    return render_template('Search_result.html',search_term=search_term,results=data,img=imgs)

@blueprint.route('/violations/<id>')
def get_vdistance(id):
    dir_name = "C:/Users/amori/Downloads/SDS/app/base/static/assets/video"
    violation = MysqlDB.get_ID(id)
    day = MysqlDB.getDay(id)
    img = MysqlDB.get_Image(id)
    vid = MysqlDB.get_vid(id) 
    if vid != None:
        with open("vid"+str(id)+".mp4","wb") as f:
            f.write(vid)

        if not os.path.exists("C:/Users/amori/Downloads/SDS/app/base/static/assets/video/vid"+str(id)+".mp4"):
            shutil.move("C:/Users/amori/Downloads/SDS/vid"+str(id)+".mp4", 'C:/Users/amori/Downloads/SDS/app/base/static/assets/video')

        vid = "vid"+str(id)+".mp4"
        
    
    if (img is None):
        violation_img = ""
    else:    
        violation_img = base64.b64encode(img).decode('utf-8')    
    
    return render_template("Violation_Info.html", results=violation,day=day,img=violation_img, vid=vid)


@blueprint.route('/table')
def Make_table():
    dir_name = "C:/Users/amori/Downloads/SDS/app/base/static/assets/video"
    data = MysqlDB.get_all()
    imgs=[]

    for video in os.listdir("C:/Users/amori/Downloads/SDS/app/base/static/assets/video"):
        if video.endswith(".mp4"):
            os.remove(os.path.join(dir_name, video))

    for i in data:
        imgs.append(base64.b64encode(i[4]).decode('utf-8'))
    count = MysqlDB.get_No_of_rows()

    return render_template("/ui-tables.html",data=data,img=imgs,count=count)


@blueprint.route("/analysis")
def get_analytics():
    data = MysqlDB.get_all()

    mon = 0
    tue = 0
    wed = 0
    thu = 0
    fri = 0
    sat = 0
    sun = 0
    theday = 0
    jan_count = 0
    feb_count = 0
    mar_count = 0
    april_count = 0
    days = []
    types = []
    mask_count = 0
    distance_count = 0
    temperature_count = 0
    occupancy_count = 0

    for i in data:
        days.append(i[2])

    for i in data:
        types.append(i[1])

    for dd in days:
        theday = datetime.strptime(dd, "%d-%m-%Y").weekday()
        if (theday == 0):
         mon = mon + 1
        elif (theday == 1):
         tue = tue + 1
        elif(theday == 2):
         wed = wed + 1   
        elif (theday == 3):
         thu = thu + 1 
        elif (theday == 4):
         fri = fri + 1
        elif (theday == 5):
         sat = sat + 1
        elif(theday == 6): 
         sun = sun + 1
        else:
            flash("Unknown date")
    days_count = [sat,sun,mon,tue,wed,thu,fri]

    for t in types:
        if (t.lower() == "mask"):
            mask_count = mask_count + 1
        elif (t.lower() == "distance"):
            distance_count = distance_count + 1
        elif(t.lower()== "temperature"):
            temperature_count = temperature_count + 1
        elif(t.lower()== "occupancy"):
            occupancy_count = occupancy_count + 1
        else:
            flash("Uknown type")
    types_count =[mask_count,distance_count,temperature_count,occupancy_count]

    for m in days:
        month = datetime.strptime(m,'%d-%m-%Y').strftime("%B")
        if (month.lower() == "january"):
            jan_count = jan_count + 1
        elif (month.lower()=="february"):
            feb_count = feb_count + 1
        elif (month.lower() == "march"):
            mar_count = mar_count + 1
        elif (month.lower() == "april"):
            april_count = april_count + 1
        else:
            None    
    months_count = [jan_count,feb_count,mar_count,april_count]
   

    return render_template('/analytics.html',days=days_count,types=types_count,months=months_count,data=data)



# @blueprint.route("/local_test")   
# def local_test():
#     #face mask
#     return redirect("http://192.168.43.175:5000/video_feed")
   
@blueprint.route("/local_test")   
def local_test():
    #face mask
    return redirect("http://192.168.43.175:5000/video_feed")
    
@blueprint.route("/local_test2")   
def local_test2():
    #thermal 
    return redirect("http://192.168.43.178:5002/video_feed")

@blueprint.route("/local_test3")   
def local_test3():
    # counter
    return redirect("http://192.168.43.175:5003/video_feed")

@blueprint.route("/local_test4")    
def local_test4():
    # social distancing
    return redirect("http://192.168.43.175:5004/video_feed")


@blueprint.route('/noti', methods=["POST","GET"])
def noti():
    print("i am at noti")
    # img2 = 'C:/Users/amori/Downloads/SDS/app/base/static/assets/img/mask.png'
    # img = cv2.imread(r"C:/Users/amori/Downloads/SDS/app/base/static/assets/img/mask.png")
    # print(img)
    # pyautogui.click(pyautogui.center(pyautogui.locateOnScreen(img3)))
    #pyautogui.moveTo(335,116)
    # pyautogui.press('home')
    pyautogui.click(98,700)
    return 'OK'

