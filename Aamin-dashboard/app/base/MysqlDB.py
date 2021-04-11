from datetime import datetime,date
from flask import Flask,render_template,flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData, Table, desc, event
from sqlalchemy.orm import mapper, sessionmaker
import argparse
from cv2 import cv2
import calendar
import base64




# problem with mac os + mysql remove in rasberypi
# using pip install PyMySQL
#import pymysql
#pymysql.install_as_MySQLdb()



class sds(object):
    pass

def loadSession():
    """"""    
    # to conncet with mysql that run on raperry pi :
    # engine = create_engine('mysql://root:pass@192.168.1.10:3306/sds', echo=True) 
    engine = create_engine('mysql://root:''@localhost:3308/sds',echo=False)
    
    metadata = MetaData(engine)

    metadata.reflect(bind=engine)
    conn = engine.connect()

    violations = Table('violations', metadata, autoload=True)
    mapper(sds, violations)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session,conn,violations



session,conn,violations = loadSession()




def get_No_of_rows():
    session.rollback()
    result = session.query(violations.c.ID).count()
    return result

def get_ID_all():
    session.rollback()
    result = session.query(violations.c.ID).all()
    return result

def get_all():
    # chnge the timeout in mysql.conf to 5000
    session.rollback()
    result = session.query(violations).all()
      
    return result

def get_ID(id):
    data = {}
    session.rollback()
    try:
        result = session.query(violations).filter_by(ID = id).first()
        data ={
            "ID":result.ID,
            "Type": result.Type,
            "Date":result.Date,
            "Time":result.Time,
            "Image":result.Image,
            "Video":result.Video,
            "Temperature":result.Temperature
           
           
        }
    except:
        flash("The ID: "+id+" Does not exist")
    return  data

def get_Type_all():
    session.rollback()
    result =  session.query(violations.c.Type).all()  
    data = []

    for vtype in result:
        data.append({
        "ID":vtype.ID,
        "Type": vtype.Type,
        "Date":vtype.Date,
        "Time":vtype.Time,
        "Image":vtype.Image,
        "Video":result.Video,
        "Temperature":result.Temperature
        })

    return  data 
     

def get_Type(type):
    session.rollback()
    result = session.query(violations).filter_by(Type = type).all()
    data = []

    for vtype in result:
        data.append({
        "ID":vtype.ID,
        "Type": vtype.Type,
        "Date":vtype.Date,
        "Time":vtype.Time,
        "Image":vtype.Image,
        "Video":result.Video,
        "Temperature":result.Temperature
      
        })
    

    return  data

 

def getDay(id):
    result = get_ID(id)
    date=(result["Date"])
    day = datetime.strptime(date, '%d-%m-%Y').weekday()
    theday = ""
    if (day == 0):
        theday = "Monday"
    elif (day == 1):
        theday = "Tuesday"
    elif(day == 2):
        theday = "Wednesday"    
    elif (day == 3):
        theday = "Thursday"  
    elif (day == 4):
        theday = "Friday"
    elif (day == 5):
        theday ='Saturday'
    elif (day == 6):
        theday = "Sunday"    
    else:
        theday = "Uknown"

    return theday



def get_Image(id):
    session.rollback()
    result = session.query(violations).filter_by(ID = id).first()
    return result.Image 


def get_vid(id):
    session.rollback()
    result = session.query(violations).filter_by(ID = id).first()
    return result.Video 

def get_all_images():
    session.rollback()
    result = session.query(violations.c.Image).all()
    return result


