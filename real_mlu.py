from flask import Flask, redirect, url_for, render_template, request, session, flash,g
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage
from datetime import timedelta
#from second import second #This is what you can use for Blueprints
from vosk import Model, KaldiRecognizer, SetLogLevel
import sys
import os
import wave
import contextlib
import morfessor
import pandas as pd
import smtplib
import os
from dotenv import load_dotenv
#from flask_wtf import FlaskForm
#from wtforms import TextField, BooleanField, TextAreaField, SubmitField

load_dotenv()
app = Flask(__name__)
app.secret_key =os.getenv("SECRET")
app.permanent_session_lifetime = timedelta(minutes=5)  #How long you want to store session data? Put here

####HOME PAGE#######
@app.route("/",methods=["GET","POST"])
@app.route("/home",methods=["GET","POST"])
def home():
    return render_template('index.html')

####UPLOAD--Sending to Transcript#####
@app.route('/upload')
def upload_filez():
   return render_template('uploader.html')
    
@app.route('/uploader', methods = ['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
      f = request.files['file']
      f.save(secure_filename(f.filename))
      try:
        wf = wave.open(f.filename, "rb")
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
            message="Your wav file needs to have 1 channel. Please try again."
        else:
            model = Model("model")
            rec = KaldiRecognizer(model, wf.getframerate())
            rec.SetWords(True)
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    pass
                else:
                    pass

            text=rec.FinalResult()
            time=text.split('}]',1)
            time=time[-2]
            time=time.split('}, {')
            time=time[-1]
            time=time.split(',')
            time=time[-3]
            time=time.split(': ')
            time=(time[-1])
            time=float(time)
            session['final_time']=time 
            new_text=text.rsplit(']',1)
            new_text=new_text[-1]
            new_text=new_text[13:-2]    
            length=len(new_text.split())
            transcript=new_text
            session['transcript']=transcript
            return render_template('transcript.html',transcript=transcript)
      except:
        message="File wasn't the correct format. Try again."
        return render_template("uploader.html",message=message)
 
###Transcript--Processing##   
@app.route("/transcript",methods=["GET","POST"])
def process_it():
    if request.method == 'POST':
        f = request.form['transcript']
        if f=="":
            message2="Please enter your transcript again."
            return render_template('transcript.html',message2=message2)
        else:
            model_file = "model.bin"
            io = morfessor.MorfessorIO()
            model = io.read_binary_model_file(model_file)
            body=f 
            utt=len(body.split('.'))
            text=body.split()
            text=list(text)
            morphemes=[]
            for morph in text:
                morphemes.append(model.viterbi_segment(morph)[0])
            morphs=[]
            for i in morphemes:
                for j in i:
                    morphs.append(j)
            number=len(morphs) #number of morphemes
            words=len(text) #number of words
            utt=len(body.split('.')) #number of utterances
            utt=utt-1
            if body=="":
                body="NA"
            elif utt<=0:  
                utt='NA'
                mlu='NA'
            elif words<=0:
                words='NA'
                wpm='NA'
            elif number<=0:
                number="NA"
                wpm='NA'
            else:
                mlu=round((number/utt),2)
            if session.get('final_time') and session.get('transcript') is not None:
                final_time=session['final_time']
                transcript=session['transcript']
                wpm=float(round((words/final_time),2))
            else:
                transcript='NA'
                final_time='NA'
                wpm='NA'
            results=f"Transcript: {body}\nMean Length Utterance (MLU): {mlu}\nWords Per Minute (WPM): {wpm}\nTotal Time (sec): {final_time}\nNumber of Morphemes: {number}\nNumber of Words: {words}\nNumber of Utterances: {utt}"
            session['results']=results
            return redirect(url_for('.results'))
    return render_template('transcript.html',message2="")

####Results#####
@app.route("/results",methods=['GET','POST'])
def results():
    results=session['results']
    session.pop('final_time',None)
    session.pop('transcript',None)
    session.pop('results',None)
    return render_template('results.html',results=results)

####AboutUs#####
@app.route("/aboutus")
def aboutus():
    return render_template('aboutus.html')

####FAQS#####
@app.route("/faqs")
def faqs():
    return render_template('faqs.html')

####CONTACT US####

@app.route("/contactus", methods=['GET','POST'])
def contactus():
    return render_template('contactus.html')
@app.route("/form",methods=["POST"])
def form():
    email=request.form["email"]
    message=request.form["message"]
    text="MLU Calculator\nSomeone sent you a message\nEmail: "+email+"\nMessage:\n"+message
    if not email or not message:
        info_text="Please enter all the correct information."
        return render_template("contactus.html",info_text=info_text)
    else:
        server=smtplib.SMTP("smtp.gmail.com",587)
        server.starttls()
        server.login("wozniakneel@gmail.com",f'{os.getenv("PASSWORD")}')
        server.sendmail("wozniakneel@gmail.com","wozniakneel@gmail.com",text)
        info_text="Message sent!"
        return render_template("contactus.html",info_text=info_text)

if __name__ == "__main__":
	app.run(debug=True)