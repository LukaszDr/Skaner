from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    measures = db.relationship('Measure', backref='author', lazy='dynamic')

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return unicode(self.id)  # python 2
        except NameError:
            return str(self.id)  # python 3

    def __repr__(self):
        return '<Name %r>' % (self.nickname)

class Measure(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime)
    minVal = db.Column(db.Integer)
    maxVal = db.Column(db.Integer)
    scale = db.Column(db.Integer)
    active = db.Column(db.Boolean)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    photos = db.relationship('Photo', backref='title', lazy='dynamic')

    def __repr__(self):
        return '<Name %r>' % (self.title)

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    photopath = db.Column(db.String(50))
    value_x = db.Column(db.Float)
    value_y = db.Column(db.Float)
    calculated=db.Column(db.Boolean)
    measure_id = db.Column(db.Integer, db.ForeignKey('measure.id'))
    points = db.relationship('Point', backref='photopath', lazy='dynamic')

    def __repr__(self):
        return '<Point %r>' % (self.photopath)

class Point(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    value_x = db.Column(db.Float)
    value_y = db.Column(db.Float)
    photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'))

    def __repr__(self):
        return '<Point %r>' % (self.value_x)




