from email import message
from sre_constants import SUCCESS
from flask import Flask, render_template, flash, redirect,url_for, session, logging, request
import random
from flask_mysqldb import MySQL
from matplotlib.pyplot import text
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import os
from werkzeug.utils import secure_filename
con = Flask(__name__)
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("You need to be logged in before visit this route!", "danger")
            return redirect(url_for('login'))
    return decorated_function
class LoginForm(Form):
    nickname= StringField(validators= [validators.DataRequired(message= "Enter your nickname")])
    password= PasswordField(validators= [validators.DataRequired(message="Enter your password")])
class RegisterForm(Form):
    nickname= StringField(validators=[validators.DataRequired(message= "You must enter a nickname")])
    password= PasswordField(validators= [validators.DataRequired(message= "You must enter a password"), validators.EqualTo('password_confirm')])
    password_confirm = PasswordField(validators= [validators.DataRequired(message= "You must fill this place")])
    friend_code = StringField(validators= [validators.DataRequired(message= "Enter your friend code!")])
class TextPost(Form):
    post_title = StringField(validators=[validators.DataRequired(message="You must enter a post title")])
    post_content = TextAreaField(validators= [validators.DataRequired(message= "You must enter a post content")])
class UploadImage(Form):
    image_title = StringField(validators=[validators.DataRequired(message= "You must enter a image title to this post!")])
class UploadVideo(Form):
    video_title = StringField(validators=[validators.DataRequired(message= "You must enter a video title to this post!")])
class CreateCode(Form):
    code = StringField(validators=[validators.DataRequired(message="You must enter a code")])

con.secret_key = "con"
con.config["MYSQL_HOST"] = "localhost"
con.config["MYSQL_USER"] = "root"
con.config["MYSQL_PASSWORD"] = ""
con.config["MYSQL_DB"] = "con"
con.config["MYSQL_CURSORCLASS"] = "DictCursor"
con.config["IMAGE_UPLOADS"] = "E:/websiteproject/CellarofNosen/static"
con.config["VIDEO_UPLOADS"] = "E:/websiteproject/CellarofNosen/static"
con.config["ALLOWED_IMAGE_EXTENSIONS"] = ["PNG", "JPG", "JPEG", "GIF"]
con.config["ALLOWED_VIDEO_EXTENSIONS"] = ["MP4", "MOV"]

def allowed_image(filename):
    if not "." in filename:
        return False
    ext = filename.rsplit(".", 1)[1]

    if ext.upper() in con.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return True
    else:
        return False

def allowed_video(filename):
    if not "." in filename:
        return False
    ext = filename.rsplit(".", 1)[1]

    if ext.upper() in con.config["ALLOWED_VIDEO_EXTENSIONS"]:
        return True
    else:
        return False

mysql = MySQL(con)
@con.route('/', methods = ["GET", "POST"])
def login():
    login_form= LoginForm(request.form)
    if request.method == "POST":
        nickname_entered = login_form.nickname.data
        password_entered = login_form.password.data
        cursor = mysql.connection.cursor()
        query = "Select * From users where nickname = %s"
        result = cursor.execute(query, (nickname_entered,))
        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered, real_password):
                session["logged_in"] = True
                session["username"] = nickname_entered
                flash("Login Successful!", "success")
                return redirect(url_for("homepage"))
            else:
                flash("Your nickname or password wrong!","danger")
                return redirect(url_for("login"))
        else:
               flash("Your nickname or password wrong!","danger")
               return redirect(url_for("login")) 
    else:
        return render_template('login.html', form= login_form)
@con.route('/homepage')
@login_required
def homepage():
    with open("messages.txt") as file:
        messages_list = file.readlines()
        message = random.choice(messages_list)
    cursor = mysql.connection.cursor()
    query = "Select * From posts"
    result= cursor.execute(query)
    if result > 0:
        posts = cursor.fetchall()
        return render_template('homepage.html', articles= posts, random_message = message)
    else:
        return render_template('homepage.html')
@con.route('/register', methods= ["GET", "POST"])
def register():
    register_form= RegisterForm(request.form)
    if request.method == "POST" and register_form.validate():

        userNickName = register_form.nickname.data
        userPassword = sha256_crypt.encrypt(register_form.password.data)
        #userEmail = register_form.email.data
        userRegisterCode = register_form.friend_code.data

        cursor = mysql.connection.cursor()

        look_for_nickname = "SELECT * FROM users WHERE nickname= %s"

        nickname_result = cursor.execute(look_for_nickname, (userNickName, ))

        print(nickname_result)

        if nickname_result == 0:
            #look_for_email = "SELECT * FROM users WHERE email= %s"
            #email_result = cursor.execute(look_for_email, (userEmail, ))

            #print(email_result)

            task_code = "Select * From friendcode where code= %s"
            code_result = cursor.execute(task_code, (userRegisterCode, ))

            if code_result != 0:
                is_code_taken_task = "Select * From friendcode where code=%s"

                cursor.execute(is_code_taken_task, (userRegisterCode,))

                info = cursor.fetchone()
                mysql.connection.commit()
                cursor.close()

                if str(info['used_by']) == '':
                    cursor = mysql.connection.cursor()
                    fill_used_by_task = "UPDATE friendcode SET used_by = %s WHERE code= %s"     
                    cursor.execute(fill_used_by_task, (userNickName, userRegisterCode))

                    query= "Insert into users(nickname, password, rank) VALUES(%s, %s, %s)"
                    cursor.execute(query, (userNickName, userPassword, "User"))
                    mysql.connection.commit()
                    cursor.close()
                    return redirect(url_for("login"))
                else:
                    flash(message= "Code already used!", category="danger")
                    return redirect(url_for("register"))
            else:
                return redirect(url_for("register"))
        #else:
        #    flash(message= "Email already taken!", category="danger")
        #    return redirect(url_for("register"))
        else:
            flash(message= "Nickname already taken!", category="danger")
            return redirect(url_for("register"))
    else:
        return render_template('register.html', form= register_form)
@con.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))
@con.route('/account')
@login_required
def account():
    cursor = mysql.connection.cursor()
    query = "Select * From posts where posted_by = %s"
    result = cursor.execute(query, (session["username"], )) 
    if result > 0 :
        posts = cursor.fetchall()
        return render_template('account.html', articles= posts)
    else:
        return render_template('account.html')
@con.route('/upload-text', methods= ["GET", "POST"])
@login_required
def upload_text():
    text_post = TextPost(request.form)
    if request.method == "POST" and text_post.validate():
        title_of_textpost = text_post.post_title.data
        content_of_textpost = text_post.post_content.data
        cursor = mysql.connection.cursor()
        query = "Insert into posts(post_title, post_content, posted_by) VALUES(%s, %s, %s)"
        cursor.execute(query, (title_of_textpost, content_of_textpost, session["username"]))
        mysql.connection.commit()
        cursor.close()
        flash("The post commited succsessfully", "success")
        return redirect(url_for('account'))
    else:
        return render_template('upload_text.html', form= text_post)     
@con.route('/upload-image', methods = ["GET", "POST"])
def upload_image():
    image_form = UploadImage(request.form)
    if request.method == "POST":
        title_of_image= image_form.image_title.data
        if request.files:
            image= request.files["image"]
            if image.filename == "":
                print("Image must have a name!")
                return redirect(request.url)
            if not allowed_image(image.filename):
                print("Wrong extension")
                return redirect(request.url)
            else:
                filename= secure_filename(image.filename)
                file_location = "/static/" + filename
                print(file_location)
                image.save(os.path.join(con.config["IMAGE_UPLOADS"], filename))
            print("Image saved!")
            cursor = mysql.connection.cursor()
            query = "Insert into posts(post_title,posted_by,isitimage, post_location) VALUES(%s, %s, %s, %s)"
            cursor.execute(query, (title_of_image, session['username'],'yes', file_location))
            mysql.connection.commit()
            return redirect(request.url)
    else:
        return render_template("upload_image.html", form= image_form)
@con.route('/post/<string:id>')
@login_required
def post_detail(id):
    cursor = mysql.connection.cursor()
    query = "Select * From posts where post_id = %s"
    result = cursor.execute(query, (id, ))

    if result > 0:
        post = cursor.fetchone()
        return render_template("post.html", content= post)
    else:
        return render_template("post.html")
@con.route('/upload-video', methods= ["GET", "POST"])
@login_required
def upload_video():
    video_form = UploadVideo(request.form)
    if request.method == "POST":
        title_of_video= video_form.video_title.data
        print(title_of_video)
        if request.files:
            video= request.files["video"]
            if video.filename == "":
                print("Video must have a name!")
                return redirect(request.url)
            if not allowed_video(video.filename):
                print("Wrong extension")
                return redirect(request.url)
            else:
                filename= secure_filename(video.filename)
                file_location = "/static/" + filename
                print(file_location)
                video.save(os.path.join(con.config["VIDEO_UPLOADS"], filename))
            print("Video saved!")
            cursor = mysql.connection.cursor()
            query = "Insert into posts(post_title,posted_by,isitvideo, post_location) VALUES(%s, %s, %s, %s)"
            cursor.execute(query, (title_of_video, session['username'],'yes', file_location))
            mysql.connection.commit()
            return redirect(request.url)
    else:
        return render_template("upload_video.html", form= video_form)
@con.route("/create-code", methods = ["GET", "POST"])
def create_code():
    friend_code = CreateCode(request.form)
    if request.method == "POST" and friend_code.validate():
        code = friend_code.code.data

        cursor = mysql.connection.cursor()

        query = "Select * From friendcode where code = %s"

        result = cursor.execute(query, (code, ))

        if result == 0:
            new_task = "Insert into friendcode(code,created_by) VALUES(%s, %s)"
            result = cursor.execute(new_task, (code, session["username"]))
            mysql.connection.commit()
            return redirect(url_for("account"))
        else:
            print("This code taken before you!")
    else:
        return render_template("create_code.html", form= friend_code)
@con.route('/about')
def about():
    return render_template("about.html")
@con.route('/search', methods= ["GET", "POST"])
def search():
    if request.method == "GET":
        return render_template(url_for('homepage'))
    else:
        keyword = request.form.get('keyword')
        cursor = mysql.connection.cursor()
        task = "Select * From posts where post_title like '%"  + keyword +"%'"
        result = cursor.execute(task)
        if result == 0:
            flash("Couldn't find anything ):", "warning")
            return redirect(url_for("homepage"))
        else:
            posts = cursor.fetchall()
            return render_template("post.html", content= posts)    
if __name__ == "__main__":
    con.run(debug=True)