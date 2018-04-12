from flask import render_template, flash, redirect, url_for, session, request
from werkzeug.utils import secure_filename
from app import app
from app.fb_objects import User, UserLoginFailedException, UsernameAlreadyInUseException, EmailAlreadyInUseException, Post, Friendship
import os, datetime, sqlite3

@app.route("/")
def index():
    return redirect(url_for('home'))

@app.route('/home')
def home():

    if 'activeUserID' not in session:

        return redirect(url_for('login'))

    active_user = User(session['activeUserID'])

    return render_template("home.html", user=active_user, title="{0} {1}'s Feed".format(active_user.first_name, active_user.surname))


@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == "POST":
        try:
            user = User.login_user(request.form['email'], request.form['password'])
            session['activeUserID'] = user.id
            return redirect(url_for('home'))

        except UserLoginFailedException:
            flash("Email and Password combination incorrect.")
            return redirect(url_for('login'))

    else:
        return render_template('login.html', no_nav_bar=True)


@app.route('/logout')
def logout():
    if 'activeUserID' in session:
        active_user = User(session['activeUserID']).update_last_active()
        del session['activeUserID']

    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == "POST":

        # Check if password and confirm password match

        if request.form['password'] != request.form['password_confirmation']:
            flash("Password and password confirmation do not match!")
            # form data is passed to template so that users do not need to re-enter all the data again
            return render_template('register.html', formdata=request.form)

        if len(request.form['password']) < 8:
            flash("Password is less than 8 characters in length. Please enter a longer password.")
            # form data is passed to template so that users do not need to re-enter all the data again
            return render_template('register.html', formdata=request.form)


        # Check if profile picture has been included and, if so, save it to the media uploads folder
        profile_pic_file = request.files['profile_pic']

        if profile_pic_file and '.' in profile_pic_file.filename and profile_pic_file.filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']:

            filename = str(datetime.datetime.utcnow()).replace(":", "_") + "_" + profile_pic_file.filename
            filename = secure_filename(filename)
            profile_pic_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        else:
            flash("No profile picture provided of an accepted type (png, jpg, gif)")
            return render_template('register.html', formdata=request.form)

        # Now register the new user, passing the path to the profile picture for the new user
        try:

            registered_user = User.register_user(request.form['username'], request.form['email'], request.form['password'], request.form['first_name'], request.form['surname'], filename, request.form['bio'], request.form['dob'])
            flash("User {} registered!".format(registered_user.username))

            return redirect(url_for('login'))

        # If registration fails (due to username or password already being taken), inform users and remove saved
        # profile pic before redirecting to registration page for user to try again.

        except EmailAlreadyInUseException:
            flash("An account has already been registered with this email address")
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return render_template('register.html', formdata=request.form)

        except UsernameAlreadyInUseException:
            flash("An account has already been registered with this username")
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return render_template('register.html', formdata=request.form)


    else:
        return render_template("register.html", no_nav_bar=True, title="Registration")


