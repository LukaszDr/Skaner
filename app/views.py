from flask import make_response, render_template, flash, redirect, session, url_for, request, g, send_from_directory, send_file
from flask_login import login_user, logout_user, current_user, login_required
from app import app, db, lm, oid, models
import time
from .forms import LoginForm
from .models import User
from .models import Measure
from .models import Photo
from .models import Point
from encoder import encoder
import RPi.GPIO as GPIO
import datetime
import cv2
import os
import thread
import shutil

db.session=db.create_scoped_session()
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
    #db.session=db.create_scoped_session()
    
    photo=Photo.query.filter_by(id=photo_id).first()
    photo.calculated=True
    db.session.commit()
    img = cv2.imread(photo.photopath,0)
    edges=cv2.Canny(img,measure.minVal,measure.maxVal)
    path = os.path.basename(photo.photopath)
    path = '/home/pi/skaner/app/photos/' + measure.title + '/edges/' + path
    print path
    cv2.imwrite(path,edges)


    #skalowanie i dodwanie

    #sprawdzam rozdzielczosc
    rowcount=edges.shape[0]
    columncount=edges.shape[1]
    

    print ("przed petla")
    #dodaje punkty
    for i in range(50,rowcount-51):
        for j in range(50,columncount-51):
            if(edges[i,j]!=0):
                point= Point(value_x=photo.value_x+(i*measure.scale),
                            value_y=photo.value_y+(j*measure.scale),
                            photopath=photo)
                db.session.add(point)
                db.session.commit()
    print ("po petli")
    return 0


#watek do sprawdzania obrabiania
def computecheck(threadname, measure):
    global current_measure_id
    measure = Measure.query.filter_by(id=current_measure_id).first()
    while(measure.active):
        try:
            p= Photo.query.filter_by(measure_id=measure.id).filter_by(calculated=False)
            for i in p:
                thread.start_new_thread(compute, (i.photopath, i.id , measure, ))
                print"sa lipy"
            time.sleep(1)
        except:
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

        #wczytuje pozostale dane nt pomiaru
        m_minimal=request.form['min_value']
        m_maximal=request.form['max_value']
        m_scale=request.form['scale']

        #check if values are numbers
        try:
            float(m_minimal)
        except:
            m_minimal=400
            flash("value must be numbers. Typical value assigned to uncorrect values. Try editing")
            
        try:
            float(m_maximal)
        except:
            m_maximal=500
            flash("value must be numbers. Typical value assigned to uncorrect values. Try editing")
            
        try:
            float(m_scale)
        except:
            m_scale=0.08
            flash("value must be numbers. Typical value assigned to uncorrect values. Try editing")
        
        #assign typical values if None
        if m_minimal is None or m_minimal == "":
            m_minimal=400
        if m_maximal is None or m_minimal == "":
            m_maximal=500
        if m_scale is None or m_minimal == "":
            m_scale=0.08
        
        #czyszcze encodery    
        encodery.clear()
        encoderx.clear()
        #tworze nowy
        measure= Measure(title=processed_text,
                         timestamp=datetime.datetime.utcnow(),
                         #DO USTALENIA!!!!
                         minVal=m_minimal,
                         maxVal=m_maximal,
                         scale=m_scale,
                         active=True,
                         author=user)
        db.session.add(measure)
        db.session.commit()
        flash('New measure added! You can add points now.')
        current_measure_id = measure.id
        print current_measure_id

        #start watku sprawdzajacego czy jest cos do przetworzenia
        
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
    flash(s.join(('Added photo for measure:',str(m.title))))
    session['selected_id']=m.id
    return redirect(url_for('points'))

@app.route('/points')
@login_required
def points():
    global current_measure_id
    m = Measure.query.filter_by(id=current_measure_id).first()
    p = m.photos.all()
    return render_template("points.html",
                           title='Points',
                           m=m,
                           p=p)

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

@app.route('/database', methods=['POST'])
@login_required
def database_post():
    #wyciagam info z html
    info = str(request.form['submit'])
    selected_id=info.replace(info[:1],'')
    info=info[:1]
    selected_id=int(selected_id)
    m = Measure.query.filter_by(id=selected_id).first()

    #usuwania
    if(info=="d"):
        allp=m.photos.all()
        for p in allp:
            allpoints=p.points.all()
            for point in allpoints:
                db.session.delete(point)
            print p.points.all()
            db.session.delete(p)

        db.session.delete(m)
        db.session.commit()
        #usuwam pliki
        try:
            path = '/home/pi/skaner/app/photos/' + m.title + '/'
            shutil.rmtree(path)
        except:
            print 'directory already deleted'
        s=" "
        flash(s.join(('Succesfuly deleted measure:',str(selected_id))))
        return redirect(url_for('database'))

    #wyswietlanie
    else:
        #cookie?
        session['selected_id']=selected_id
        s=" "
        return redirect(url_for('info', selected_id=selected_id))    


@app.route('/info')
@login_required
def info():
    selected_id=session['selected_id']
    #return send_file("a.png", as_attachment=True)
    
    m = Measure.query.filter_by(id=int(selected_id)).first()
    path = '/home/pi/skaner/app/photos/' + m.title + '/results of ' + m.title+ '.csv'
    try:
        F = open(path, 'w')
        photos=m.photos.all()
        for photo in photos:
            points=photo.points.all()
            for point in points:
                F.write(str(point.value_x)+(",")+str(point.value_y)+"\n")
        F.close
        print path
    except:
        flash("This measurement has no photos taken!")
    
    return render_template("info.html",
                           m=m)

@app.route('/download')
@login_required
def download():
    selected_id=session['selected_id']
    m = Measure.query.filter_by(id=int(selected_id)).first()
    try:
        path = '/home/pi/skaner/app/photos/' + m.title + '/results of ' + m.title+ '.csv'
        return send_file(path, as_attachment=True)
    except:
        flash("Cannot generate file! This measurement has no photos taken!")
        return render_template("info.html",
                               m=m)
    
@app.route('/edit', methods=['POST'])
@login_required
def edit():
    selected_id=session['selected_id']
    selected_id=request.form['mes_id']
    m = Measure.query.filter_by(id=int(selected_id)).first()

    #wczytuje pozostale dane nt pomiaru
    m_minimal=request.form['min_value']
    m_maximal=request.form['max_value']
    m_scale=request.form['scale']
    
    #check if values are numbers
    try:
        float(m_minimal)
    except:
        m_minimal=""
        flash("value must be numbers. Value left as it is. Try editing again")
            
    try:
        float(m_maximal)
    except:
        m_maximal=""
        flash("value must be numbers. Value left as it is. Try editing again")
            
    try:
        float(m_scale)
    except:
        m_scale=""
        flash("value must be numbers. Value left as it is. Try editing again")

    change=False
    #leave values if None
    if m_minimal is None or m_minimal == "":
        m_minimal=m.minVal
    else:
        change=True
    if m_maximal is None or m_maximal == "":
        m_maximal=m.maxVal
    else:
        change=True
    if m_scale is None or m_scale == "":
        m_scale=m.scale
    else:
        change=True
        
    if change == True:
        m.minVal=m_minimal
        m.maxVal=m_maximal
        m.scale=m_scale
        db.session.commit()
        flash("editing succesfull")
        exist=False
        
        #sprawdzam czy to aktualny pomiar, jak tak to zeruje flagi przetworzenia zdjec i niszcze punkty
        if m.active==True:
            photos=m.photos.all()
            for photo in photos:
                points=photo.points.all()
                for point in points:
                    db.session.delete(point)
                photo.calculated=False
            db.session.commit()
            flash("current measure being recalculated")
        #jak nie to rbie osobny watek andzorujacy, ktory sie raz wywola i wszystko pieknie przetworzy
        else:
            flash ("old emasure being recalculated")
            
        
        return render_template("info.html",
                            m=m)    


#@app.route('/download/<path:filename>')
#@login_required
#def serve_static(filename):
 #   selected_id=session['selected_id']
    
    #root_dir=os.path.dirname(os.getcwd())
    #flash(str(filename))
  #  return send_file("a.png", as_attachment=True)

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
