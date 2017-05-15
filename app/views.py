from flask import render_template, flash, redirect, session, url_for, request, g
from flask_login import login_user, logout_user, current_user, login_required
from app import app, db, lm, oid, models
import time
from .forms import LoginForm
from .models import User
from .models import Measure
from .models import Photo
from encoder import encoder
import RPi.GPIO as GPIO
import datetime
import cv2
import os
import thread

db.session.expire_on_commit=False
GPIO.cleanup()
GPIO.setmode(GPIO.BCM)  
GPIO.setwarnings(False)
encoderx=encoder(0,25,18,25)
encodery=encoder(0,25,23,24)
allpoints=[]
current_measure_id = None


#watek przetwarzania
def compute( threadname, photo_id, measure):
    photo=Photo.query.filter_by(id=photo_id).first()
    img = cv2.imread(photo.photopath,0)
    edges=cv2.Canny(img,measure.minVal,measure.maxVal)
    path = os.path.basename(photo.photopath)
    path = '/home/pi/skaner/app/photos/' + measure.title + '/edges/' + path
    print path
    cv2.imwrite(path,edges)
    photo.calculated=True
    db.session.commit()
    print photo.photopath
    print "przetworzone"
    return 0


#watek do sprawdzania obrabiania
def computecheck(threadname, measure):
    global current_measure_id
    measure = Measure.query.filter_by(id=current_measure_id).first()
    while(measure.active):
        p= Photo.query.filter_by(measure_id=measure.id).filter_by(calculated=False)
        for i in p:
            thread.start_new_thread(compute, (i.photopath, i.id , measure, ))
            print"sa lipy"
 
        
        measure = Measure.query.filter_by(id=current_measure_id).first()
        #db.session.commit()
        time.sleep(1)
    return 0


@app.route('/new')
@login_required
def new():
    encodery.clear()
    encoderx.clear()
    user=g.user
    return render_template("new.html")

@app.route('/new', methods=['POST'])
@login_required
def new_post():
    global current_measure_id
    user=g.user
    name=request.form['measure_name']
    processed_text=name.upper()
    if processed_text is None or processed_text == "":
        flash('Invalid name. Try again')
        return redirect(url_for('new'))
    measure= Measure.query.filter_by(title=processed_text).first()
    if measure is None:
        #niekatywnosc
        m= Measure.query.filter_by(active=True)
        for i in m:
            i.active=False
            db.session.commit()
            print i.title

        #tworze nowy
        measure= Measure(title=processed_text,
                         timestamp=datetime.datetime.utcnow(),
                         #DO USTALENIA!!!!
                         minVal=400,
                         maxVal=500,
                         scale=0.08,
                         active=True,
                         author=user)
        db.session.add(measure)
        db.session.commit()
        flash('New measure added! You can add points now.')
        current_measure_id = measure.id
        print current_measure_id
        thread.start_new_thread(computecheck, (measure.title, measure, ))
        db.session.commit()
        return redirect(url_for('points'))
    flash('This name already exists')
    return redirect(url_for('new'))

                           

@app.route('/show')
@login_required
def show():
    return render_template("value.html",
                           title='Value',
                           encodery=encodery,
                           encoderx=encoderx,)

@app.route('/addp')
@login_required
def addp():
    global current_measure_id
    m = Measure.query.filter_by(id=current_measure_id).first()
    if m is None:
        flash('Make a new measure first!')
        return redirect(url_for('new'))
    allpoints.append([encoderx.value(),encodery.value()])
    filename=time.strftime("%Y%m%d-%H%M%S")
    
    cam = cv2.VideoCapture(0)
    s, im=cam.read()
    path = '/home/pi/skaner/app/photos/' + m.title
    try:
        os.stat(path)
    except:
        os.mkdir(path)
        os.mkdir(path + '/edges')
    path=path + '/' + filename + '.png'
    cv2.imwrite(path, im)
    photo = Photo(photopath=path,
                  value_x=encoderx.value(),
                  value_y=encodery.value(),
                  calculated=False,
                  title=m)
    s=" "
    db.session.add(photo)
    db.session.commit()
    flash(s.join(('Points for measure:',str(m.title))))
    return redirect(url_for('points'))

@app.route('/points')
@login_required
def points():
    return render_template("points.html",
                           title='Points',
                           allpoints=allpoints)

@app.route('/')
@app.route('/index')
@login_required
def index():
    user = g.user
    posts = [  # fake array of posts
        { 
            'author': {'nickname': 'John'}, 
            'body': 'Beautiful day in Portland!' 
        },
        { 
            'author': {'nickname': 'Susan'}, 
            'body': 'The Avengers movie was so cool!' 
        }
    ]
    return render_template("index.html",
                           title='Home',
                           user=user,
                           posts=posts)

@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    if g.user is not None and g.user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        return oid.try_login(form.openid.data, ask_for=['nickname', 'email'])
    return render_template('login.html', 
                           title='Sign In',
                           form=form,
                           providers=app.config['OPENID_PROVIDERS'])



@app.route('/database', methods=['GET'])
@login_required
def database():
    users = models.User.query.all()
    user = g.user
    measures = user.measures.all() #models.Measure.query.all()
    db.session.commit()
    return render_template("database.html",
                           title='database',
                           users=users,
                           measures=measures)

@app.route('/logout')
def logout():
    logout_user()
    db.session.commit()
    return redirect(url_for('index'))


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@oid.after_login
def after_login(resp):
    if resp.email is None or resp.email == "":
        flash('Invalid login. Please try again.')
        return redirect(url_for('login'))
    user = User.query.filter_by(email=resp.email).first()
    if user is None:
        nickname = resp.nickname
        if nickname is None or nickname == "":
            nickname = resp.email.split('@')[0]
        user = User(nickname=nickname, email=resp.email)
        db.session.add(user)
        db.session.commit()
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    login_user(user, remember = remember_me)
    return redirect(request.args.get('next') or url_for('index'))

@app.before_request
def before_request():
    g.user = current_user
