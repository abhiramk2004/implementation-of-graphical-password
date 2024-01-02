from flask import Flask,render_template,url_for,redirect,request,flash,session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from PIL import Image
import imagehash
from flask_wtf import FlaskForm,CSRFProtect
from wtforms import StringField, FileField, IntegerField,SubmitField,TextAreaField
from wtforms.validators import DataRequired
import io,secrets
#from flask_bcrypt import Bcrypt
from datetime import timedelta
image_type = ('jpg', 'jpe', 'jpeg', 'png', 'gif', 'svg', 'bmp')
def is_image(image_type,image_name):
    return image_name.split('.')[-1] in image_type
def hybrid_hash(image):   
    phash=imagehash.phash(image)
    diffhash=imagehash.dhash(image)
    hybrid_hash_value=str(phash)+str(diffhash)
    return hybrid_hash_value
app=Flask(__name__)
app.secret_key=secrets.token_hex(32)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.sqlite3"
app.config["SQLALCHEMY_TRACKS_MODIFICATIONS"] = False
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes = 5)

db=SQLAlchemy(app)
#bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)
class Myform(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    image1 = FileField('Image1', validators=[DataRequired()])
    image2 = FileField('Image2', validators=[DataRequired()])
    image3 = FileField('Image3', validators=[DataRequired()])
    image4 = FileField('Image4', validators=[DataRequired()])
    image5 = FileField('Image5', validators=[DataRequired()])
    image6 = FileField('Image6', validators=[DataRequired()])
    image7 = FileField('Image7', validators=[DataRequired()])
    image8 = FileField('Image8', validators=[DataRequired()])
    image9 = FileField('Image9', validators=[DataRequired()])
    full_name = StringField()
    other_details = TextAreaField()
    age = IntegerField('age')
    submit = SubmitField('submit')

class users(db.Model):
    username = db.Column(db.String(100),primary_key=True,nullable=False)
    password_hash=db.Column(db.String(500))
    attempt = db.Column(db.Integer)
    full_name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    other_details = db.Column(db.String(200))
    def __init__(self,username,password_hash,full_name="",age=18,other_details=""):
        self.username = username
        self.password_hash = password_hash
        self.attempt= 0
        self.full_name = full_name
        self.age = age
        self.other_details = other_details
@app.route("/")
def index():
    return render_template("index.html")
@app.route("/logout/<username>")
def logout(username):
     if ('username' in session):
        return render_template("logout.html",username=session.pop("username",None))
     else:
        flash("user already logged out.Please login once more","message")
        return redirect(url_for("login"))
@app.route("/login")
def login():
    form = Myform()
    return render_template("login.html",form=form)
@app.route("/signup")
def signup():
    form = Myform()
    return render_template("signup.html",form=form)
@app.route("/dashboard/<username>")
def dashboard(username):
     if ('username' in session):
          usr=users.query.filter_by(username=username).first()
          return render_template("dashboard.html",username=username,full_name=usr.full_name,age=usr.age,other_details=usr.other_details)
     else:
          flash("userdata not exist.Login again")
          return redirect(url_for("login",form=Myform()))
@app.route("/viewall")
def view_all():
     return render_template("all.html",use=users.query.filter_by().all())
@app.route("/process1", methods=['POST',"GET"])
def process1():
    form = Myform(request.form)
    if ( not form.validate_on_submit):
        flash('There is some errors in your form filling,kindky resubmit it','error')
        return redirect(url_for('login'))
    username = form.username.data
    found_user = users.query.filter_by(username=username).first()
    if found_user:
        hash_value = found_user.password_hash
        total_hash = ""
        for i in range(9):
            image_key = f"image{i+1}"
            if image_key in request.files :

                image_file = request.files[image_key]
                if not is_image(image_type,image_file.filename):        
                    flash('input an image file','warning')
                    return redirect(url_for('login'),form=Myform())
                file_data = image_file.read()
                image = Image.open(io.BytesIO(file_data))
                total_hash += hybrid_hash(image)
        if hash_value==total_hash:
            flash("Login Succesful","message")
            session["username"]=username
            found_user.attempt=0
            return redirect(url_for("dashboard",username=username))
        elif (found_user.attempt<3):
            flash(f"invalid password.You have {3-found_user.attempt} attempts left",'error')
            found_user.attempt+=1
            db.session.commit()
            return redirect(url_for("login"))
        else:
            flash("Your account has been locked.Contact the admin",'warning')
            return redirect(url_for("login"))
    else:
         flash("No user found.Sign up",'error')
         return redirect(url_for("signup"))   
@app.route("/process2",methods=["POST","GET"])
def process2():
    form = Myform(request.form)
    if ( not form.validate_on_submit):
        flash('There is some errors in your form filling,kindky resubmit it','error')
        return redirect(url_for('login'))
    username = form.username.data
    if users.query.filter_by(username=username).first():
         flash("username already exists","error")
         return redirect(url_for("signup"))
    full_name = request.form.get("full_name")
    age = request.form.get("age")
    other_details = request.form.get("other_details") 
    image_list = []
    total_hash = ""
    for i in range(9):
            image_key = f"image{i+1}"
            if image_key in request.files:
                image_file = request.files[image_key]
                if not is_image(image_type,image_file.filename):        
                    flash('input an image file','warning')
                    return redirect(url_for('login'),form=Myform())
                file_data = image_file.read()
                image = Image.open(io.BytesIO(file_data))
                image_list.append(image)
                total_hash += hybrid_hash(image)
    #password_hash = bcrypt.generate_password_hash(total_hash).decode('utf-8')
    usr = users(username,total_hash,full_name,age,other_details)
    db.session.add(usr)
    db.session.commit()
    session['username'] = username
    return redirect(url_for("dashboard",username=username))
with app.app_context():
    db.create_all()
