import random
from fastapi import FastAPI ,Response,UploadFile,File,HTTPException,Form,WebSocket,WebSocketDisconnect
import smtplib 
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from pydantic import BaseModel
import cloudinary
import cloudinary.uploader
import datetime

db=sqlite3.connect('chat.db',check_same_thread=False,timeout=5)
cr=db.cursor()
cr.execute('''CREATE TABLE IF NOT EXISTS Users
         (id INTEGER PRIMARY KEY AUTOINCREMENT,Email TEXT,Password TEXT,Name TEXT,Profile TEXT,Status Text,lastsenn DATETIME)''')

app = FastAPI()
class EmailData(BaseModel):
    email: str
class uname(BaseModel):
    newname:str   
    email:str 
class dataRegister(BaseModel):
    email:str
    name:str
    password:str
    confirmPassword:str
class dataLogin(BaseModel):
    email:str
    password:str
    
class NumberData(BaseModel):
    code:str  
    email:str
    name:str
class updatePasswordData(BaseModel):
    email:str
    lastPassword:str
    newPassword:str
    confirmNewPassword:str
class searchname(BaseModel):
    search:str 
    Id:str


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True, )
cloudinary.config(
            cloud_name="dpvwrxz33",
            api_key="769168646258211",
            api_secret="ift-kdREoWE7FYkwGS2BPA9BbCY",
            secure=True,)
@app.get("/")
def read_root():
    return {"Hello": "World"}
@app.post("/register")
def register(user:dataRegister):
    if(user.password!=user.confirmPassword):
        return {"status":"Password and Confirm Password do not match"}
    elif(cr.execute("SELECT * FROM Users WHERE Email=?", (user.email,)).fetchone()):
        return {"status":"User already exists"}
    else:
        cr.execute("insert into Users (Email,Password,Name) values(?,?,?)",(user.email,user.password,user.name))
        db.commit()
        return {"message": "success register"}
@app.post("/login")
def login(user:dataLogin):    
    try:
        cr.execute("SELECT * FROM Users WHERE Email=? AND Password=?", (user.email, user.password))
        db.commit()
        user = cr.fetchone()
        if user:
            return {"status": "Login successful", "name": user[3], "email": user[1]}
        else:
            return {"status": "Invalid email or password"}
    except Exception as e:
          return {"status": "An error occurred during login", "error": str(e)}   

code=str(random.randint(10000,99999))
@app.post("/numberget")
def get_email(email:EmailData):
    server=smtplib.SMTP('smtp.gmail.com', 587,timeout=10)
    server.starttls()
    server.login("ramadangafer5@gmail.com","gbxydxqrprznqvmh")
    from_addr="ramadangafer5@gmail.com"
    message="Subject: Hello\n\n this is your Code \n\n"+code
    server.sendmail(from_addr,email.email,message)
    server.quit()
    return {"status":"Code sent to email"} 

@app.post("/nuumberpost")
def post_msg(number:NumberData):
    global code
    
    if number.code == code:
        cr.execute("SELECT * FROM Users WHERE Email=? ", (number.email,))
        user = cr.fetchone()
        db.commit()
        
        return {"status": "Code is correct","Profile":user[4],"id":user[0]}
    else:
        return {"status": "Code is incorrect"}

@app.post("/deleteAccount")
def delete_account(email:EmailData):
    cr.execute("DELETE FROM Users WHERE Email=?", (email.email,))
    db.commit()
    return {"status": "Account deleted successfully"}



@app.post("/updatePassword")
def update_password(data:updatePasswordData):
    if(data.newPassword!=data.confirmNewPassword):   
        return {"status":"New Password and Confirm Password do not match"}
    else:
         cr.execute("SELECT * FROM Users WHERE Email=? AND Password=?", (data.email, data.lastPassword))
         user = cr.fetchone()
         if(user is None):
             return {"statues":"Invalid email or password"}
         try: 
            cr.execute("UPDATE Users SET Password=? WHERE Email=?",(data.newPassword,data.email))
            db.commit()
            return {"status": "Password updated successfully"}
         except Exception as e:
             db.rollback()
             return {"status":"data base error","error":str(e)}


@app.post("/updatename")
def updatename(data:uname):
    try:
        cr.execute("UPDATE  Users SET Name=? WHERE Email=?", (data.newname, data.email,))
        db.commit()
        return {"status":"success update user Name"}
    except Exception as e:        
        return {"error":e}

@app.post("/uploadprofile")
async def uploadprofile(email:str=Form(...),file:UploadFile=File(...)):
    try:
        uploadResult=cloudinary.uploader.upload(file.file,folder="use_profiles")
        image_url=uploadResult.get("secure_url")
        cr.execute("UPDATE Users SET Profile= ? WHERE Email = ?",(image_url,email))
        db.commit()
        if(cr.rowcount==0):
           raise HTTPException(status_code=404,detail="user not found")
        return {
            "status":"success",
            "message":"profile updated seccessfully",
            "image_url":image_url
        }
    except Exception as e:
        return {"status":"error","message":str(e)}
    







class idone(BaseModel):
    id:str


mdb=sqlite3.connect('mchat.db',check_same_thread=False,timeout=5)
mcr=mdb.cursor()
mcr.execute('''CREATE TABLE IF NOT EXISTS Messages
         (IDONE TEXT,MSG TEXT,IDTWO Text,TIME TEXT)''')
 


@app.post("/chatbegin")
async def chatbegin(id:idone):
    try:
        mcr.execute("SELECT * FROM Messages WHERE IDONE=? OR IDTWO=?", (id.id,id.id))
        user=mcr.fetchall()
        mdb.commit() 
        msglist=[]
        for r in user:
            msglist.append({
                "idone":r[0],
                "msg":r[1],
                "idtwo":r[2],
                "time":r[3]
            })
        return {"data":msglist}
    except Exception as e:
        return {"error":e}    

activeConnection = {}  # تأكد أن هذا متغير عام

@app.websocket("/ws")
async def websocket_function(websocket: WebSocket):
    id = websocket.query_params.get("id")
    await websocket.accept()
    activeConnection[id] = websocket
    try:
        while True:
            cr.execute("UPDATE Users SET Status= ? WHERE id = ?",("online",int(id)))
            db.commit()
            data = await websocket.receive_json()
            mcr.execute(
                "insert into Messages (IDONE,MSG,IDTWO,TIME ) VALUES (?,?,?,?)",
                (data.get("idone"), data.get("msg"), data.get("idtwo"), data.get("time"))
            )
            mdb.commit()
            # بث الرسالة لجميع الاتصالات
            for uid, connection in activeConnection.items():
                cr.execute("SELECT * FROM Users WHERE id=? ", (int(id),))
                user = cr.fetchone()
                try:
                    await connection.send_json({
                        "idone": data.get("idone"),
                        "msg": data.get("msg"),
                        "idtwo": data.get("idtwo"),
                        "time": data.get("time"),
                        "status": user[5] if user else "unknown"
                    })
                except:
                    continue
    except WebSocketDisconnect:
        if id in activeConnection:
            del activeConnection[id]
        try:
            if id and str(id).isdigit():
                user_id = int(id)
                curreentTime = datetime.datetime.now()
                cr.execute(
                    "UPDATE Users SET Status= ? , lastsenn= ? WHERE id = ?",
                    ("offline", curreentTime, user_id)
                )
                db.commit()
            return {"curr": curreentTime}
        except Exception as e:
            print("general error")    



@app.post("/search")
async def search(name:searchname):
    search_trem=f"%{name.search}%".strip()
    if search_trem:
        try:
            cr.execute("SELECT * FROM Users WHERE Name LIKE ?", (search_trem,))
            user=cr.fetchall()
            alluser=[]
            if(user):
               for u in user:
                    alluser.append({"name":u[3],"url":u[4],"id":u[0],"status":u[5],"curr":u[6]})
               return alluser       
            else:
                return {"status":"not found"}
            
        except Exception as e:
             return {"status":"error","message":str(e)}
    else :
       return     
