

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import mapper, sessionmaker


class sds(object):
    pass

def stor_in_DB(id, type,date,time):
    """"""
    id = int(id)
    #name = "amr is cool"
    engine = create_engine('mysql+pymysql://root:''@192.168.43.253:3308/sds', echo=False)
    
    metadata = MetaData(engine)

    metadata.reflect(bind=engine)
    conn = engine.connect()
    
    violations = Table('violations', metadata, autoload=True)
    mapper(sds, violations)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    
    
    with open('violation'+str(id)+'.jpeg',"rb") as f:
        binary_img = f.read()
        
    
    
    conn.execute(violations.insert(), {"Type": type,"Date": date,"Time": time, "Image": binary_img })
    #conn.execute(violations.insert(), {"id": id,"name": name})
    print("record inserted in python")
    conn.close()
    return "succsess"




