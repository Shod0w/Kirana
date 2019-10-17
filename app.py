from fastai import *
from fastai.vision import *
import fastai
#import yaml
import sys
import random
from flask_mysqldb import MySQL
from flask import render_template, request, redirect, url_for,g,session
from io import BytesIO, StringIO
import base64
import re
from typing import List, Dict, Union, ByteString, Any
import os
import flask
from flask import Flask
from flask_mail import Mail, Message
import requests
import torch
import json
from datetime import datetime, date

#with open("src/config.yaml", 'r') as stream:
 #   APP_CONFIG = yaml.full_load(stream)

app = Flask(__name__)

app.secret_key = 'kirana'

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'aayanksinghai02@gmail.com'
app.config['MAIL_PASSWORD'] = 'Astromars1999'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'KIRANA'

mysql = MySQL(app)


def load_model(path=".", model_name="model.pkl"):
   learn = load_learner(path, model_name)
   return learn


#def load_image_url(url: str) -> Image:
 #   response = requests.get(url)
  #  img = open_image(BytesIO(response.content))
   # return img


def load_image_bytes(raw_bytes: ByteString) -> Image:
    img = open_image(BytesIO(raw_bytes))
    return img


def predict(img, n: int = 3) -> Dict[str, Union[str, List]]:
    pred_class, pred_idx, outputs = model.predict(img)
    pred_probs = outputs / sum(outputs)
    pred_probs = pred_probs.tolist()
    predictions = []
    for image_class, output, prob in zip(model.data.classes, outputs.tolist(), pred_probs):
        output = round(output, 1)
        prob = round(prob, 2)
        predictions.append(
            {"class": image_class.replace("_", " "), "output": output, "prob": prob}
       )

    predictions = sorted(predictions, key=lambda x: x["output"], reverse=True)
    predictions = predictions[0:n]
    return {"class": str(pred_class), "predictions": predictions}


@app.route('/api/classify/', methods=['POST'])
def upload_file():
    #bytes = flask.request.files['img'].read()
    #img = load_image_bytes(bytes)   
    #image_data = re.sub('^data:image/.+;base64,', '', flask.request.form['img']).decode('base64')
    image_data = base64.b64decode(re.sub('^data:image/.+;base64,', '', flask.request.form['imge']))
    #image = Image.open(StringIO(image_data))
    image = load_image_bytes(image_data)
    res = predict(image)
    return flask.jsonify(res)

@app.route('/api/classes', methods=['GET'])
def classes():
    classes = sorted(model.data.classes)
    return flask.jsonify(classes)





@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"

    response.cache_control.max_age = 0
    return response

#Session Mainting


@app.before_request
def before_request():
    g.user = None
    if 'user' in session:
        g.user = session['user']

@app.route('/getsession')
def getsession():
    if 'user' in session:
        return session['user']

    return 'Not Logged In'

@app.route('/Logout')
def Logout():
    userid = session['user']
    cur = mysql.connection.cursor()
    cur.execute("UPDATE CARTBILLING SET Active = 0 where User_Id = %s", (userid,))
    cur.connection.commit()
    session.pop('user', None)


    return render_template('index.html') 
   
### OUR PROJECT HTML FILES
@app.route('/')
def welcome():
    return render_template('index.html')

@app.route('/index')
def login():
    return render_template('index.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/forgotpin')
def forgot():
    return render_template('forgotpin.html')

@app.route('/Kirana')
def Home():
    if g.user:
        return render_template('Kirana.html')

    return render_template('index.html')

@app.route('/About')
def About():
    if g.user:
        return render_template('About.html')

    return render_template('index.html')

@app.route('/Cart')
def Cart():
    if g.user:
        cur = mysql.connection.cursor()
        userid = session['user']
        cur.execute("SELECT CARTBILLING.Bill_No, CARTBILLING.User_Id, Product_Id, Rate, Product_Name FROM ITEMBILLING, CARTBILLING where CARTBILLING.Bill_No = ITEMBILLING.Bill_no AND CARTBILLING.User_Id = %s AND CARTBILLING.Active = %s",(userid,'1',))
        data = cur.fetchall()

        billno = data[0]
        cur.execute("SELECT SUM(Rate) from ITEMBILLING where Bill_No = %s", (billno,))
        res = cur.fetchall()

        totalprice = res[0]
        return render_template('Cart.html', data = data,net = totalprice)
    
    return render_template('index.html')

@app.route('/ResetPin/')
def render_Test() -> "html":
    
    return render_template('ResetPin.html', keys = request.args.get('email'))


@app.route('/Capture')
def Capture():
    return render_template('Capture.html')


def SendEmail(ind,emailaddress = '',otp = '',):
    if ind == '1':
         msg = Message('Success [KIRANA]', sender = 'KIRANA', recipients = [emailaddress])
         msg.body = "You have successfully registered at KIRANA. \nWe will be happy to serve you to bring the best time at our KIRANA."
         msg.body += "\n \n \nWarm Regards, \n"
         msg.body += "TEAM KIRANA" 
         mail.send(msg)
         return "Email Sent"
    elif ind == '2':
        msg = Message('RESET PIN: KIRANA', sender = 'KIRANA', recipients = [emailaddress])
        msg.body = "You have recently requested for PIN Reset. \nYour One Time Password (OTP) is " + otp + "\nThe OTP will expire in 5 minutes"
        msg.body += "\n \n \nWarm Regards, \n"
        msg.body += "TEAM KIRANA" 
        mail.send(msg)
        return "Email Sent"


def GenerateCart():
    
    today = date.today()
    now = datetime.now()
    d = today.strftime("%y/%m/%d")
    dt = now.strftime("%y/%m/%d %H:%M:%S")
    #print(d1)
    #print(dt)
    nt = 0
    userid = session['user']
    active = 1
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO CARTBILLING(User_Id, BillDate, Timestamp, Net_Amount, Active) VALUES (%s,%s,%s,%s,%s)", (userid,d,dt,nt,active,))
    mysql.connection.commit()



@app.route('/GenerateCart', methods = ['POST','GET'])
def AddCart():
    if request.method == 'POST':
        print('We are adding item into the cart')
        item = request.form['item']
        #size = request.form['size']
        cur = mysql.connection.cursor()
        cur.execute("Select Product_Id, Product_Cost from PRODUCT where Product_Name like %s ", (item,))
        result = cur.fetchall()
        userid = session['user']
        id = result[0][0]
        cost = result[0][1]
        

        cur.execute("SELECT Bill_No from CARTBILLING where User_id = %s and Active = %s", (userid,1,))
        rescart = cur.fetchall()

        billno = rescart[0]         
        cur.execute("INSERT INTO ITEMBILLING (Bill_No, User_Id, Product_ID, Rate, Product_Name) VALUES (%s, %s, %s, %s, %s)",(billno,userid,id,cost,item))
        mysql.connection.commit()
        cur.execute("SELECT CARTBILLING.Bill_No, CARTBILLING.User_Id, Product_Id, Rate, Product_Name FROM ITEMBILLING, CARTBILLING where CARTBILLING.Bill_No = ITEMBILLING.Bill_no AND CARTBILLING.User_Id = %s AND CARTBILLING.Active = %s",(userid,'1',))
        data = cur.fetchall()
        cur.execute("SELECT SUM(Rate) from ITEMBILLING where Bill_No = %s", (billno,))
        res = cur.fetchall()

        totalprice = res[0]
        return render_template('Cart.html', data = data,net = totalprice)

@app.route('/RP', methods = ['POST','GET'])
def ResetPin():
    email = request.args.get('email')
    print(email)
    if request.method == 'POST':
        pin = request.form['pin']
        cur = mysql.connection.cursor()
        cur.execute("Update USER set Pin = %s where Email_Address = %s", (pin, email,))
        mysql.connection.commit()
        print("PIN successfully changed")
        return 'nothing'
        #return (url_for('login'))   


@app.route('/ForgotPin', methods = ['POST'])
def ForgotPin():
    print("I am at")
    if request.method == 'POST':
        print("POST")
        emailaddress = request.form['emailaddress']
        print(emailaddress)
        cur = mysql.connection.cursor()
        cur.execute("Select Email_Address from USER where Email_Address = %s", (emailaddress,))
        my_result = cur.fetchall()

        if cur.rowcount > 0:
            otp = str(random.randint(1111,9999))
            print(otp)
            cur.execute("Update USER set OTP = %s where Email_Address = %s", (otp, emailaddress,))
            mysql.connection.commit()
            SendEmail('2',emailaddress, otp)
            print("VERIFY OTP")

        else:
            print("This account does not exists")
            return render_template('forgotpin.html')
    return 'nothing' 

@app.route('/VerifyOTP', methods = ['POST'])
def Verify_OTP():
    print("V otp par hai")
    if request.method == 'POST':
          fotp = request.form['otp']
          emailaddress = request.form['emailaddress']
          print(fotp)
          print(emailaddress)
          cur = mysql.connection.cursor()
          cur.execute("Select OTP from USER where Email_Address = %s", (emailaddress,))
          res = cur.fetchall()
          
          if (str(res[0][0])) == fotp:
              cur.execute("Update USER set OTP = NULL where Email_Address = %s", (emailaddress,))
              mysql.connection.commit()
              cur.close()
              print("return")
              return redirect(url_for('render_Test', email = emailaddress))
              #return render_template('ResetPin.html')
              #return redirect(url_for('ResetPin',email = emailaddress))
          else:
              print('Wrong OTP')
              return 'nothing'
        
@app.route('/submit_signup', methods = ['POST'])
def submit_signup():
    if request.method == 'POST':
        fullname = request.form['fullname']
        emailaddress = request.form['emailaddress']
        mobilenumber = request.form['mobilenumber']
        pin = request.form['pin']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO USER (Full_Name, Email_Address, Mobile_Number, Pin) VALUES (%s, %s, %s, %s)", (fullname, emailaddress, mobilenumber, pin))
        mysql.connection.commit()
        cur.close()
        SendEmail('1',emailaddress)
        return redirect(url_for('Home'))
    
    return redirect(url_for('signup'))
        
    
@app.route('/submit_login', methods = ['POST'])
def submit_login():
    if request.method == 'POST':
        session.pop('user', None)
        mobilenumber = request.form['mobilenumber']
        cur = mysql.connection.cursor()
        cur.execute("SELECT Mobile_Number, Pin from USER where Mobile_Number = %s", (mobilenumber,))
        my_result = cur.fetchall()
        
        if cur.rowcount > 0:
            if (str(my_result[0][0])) == mobilenumber:
                pin = request.form['pin']
                if (str(my_result[0][1])) == pin:
                    session['user'] = mobilenumber
                    GenerateCart()
                    print("Successfully Logged In!")
                    return redirect(url_for('Home'))
                    #return render_template('Kirana.html')
                else:
                    return redirect(url_for('Home'))
        else:
            print('Account does not exists! Please Sign up')
            return redirect(url_for('index.html'))
    




model = load_model('models')

if __name__ == '__main__':
    port = os.environ.get('PORT', 8082)

    if "prepare" not in sys.argv:
        app.jinja_env.auto_reload = True
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        #app.run(debug=False, host='192.168.43.250', port=port)
        app.run(debug = True,host='192.168.29.15', port=port)
