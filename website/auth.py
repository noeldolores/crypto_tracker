from flask import Blueprint, render_template, request, flash, redirect, url_for, session, escape
from flask_login import login_user, login_required, logout_user, current_user
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .views import currency_search


auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    if 'search' in request.form:
      print(request.form['search'])
      result, bad_query = currency_search(request.form['search'])
      return render_template("login.html", user=current_user, result=result, bad_query=bad_query)

    else:
      email = str(escape(request.form.get('email')))
      password = str(escape(request.form.get('password')))

      user = User.query.filter_by(email=email).first()
      if user:
        if check_password_hash(user.password, password):
          flash('Logged in successfuly!', category='success')
          login_user(user, remember=True)
          if len(current_user.currencies) == 0:
            flash("Your Dashboard is empty! Use the search bar to find and track cryptocurrencies.", category='error')
          return redirect(url_for('views.home'))
        else:
          flash('Incorrect password, try again!', category='error')
      else:
          flash('Email does not exist.', category='error')

  return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
  session.clear()
  logout_user()
  return redirect(url_for('auth.login'))


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
  if request.method == 'POST':
    if 'search' in request.form:
      print(request.form['search'])
      result, bad_query = currency_search(request.form['search'])
      return render_template("login.html", user=current_user, result=result, bad_query=bad_query)

    else:
      email = str(escape(request.form.get('email')))
      firstName = str(escape(request.form.get('firstName')))
      password1 = str(escape(request.form.get('password1')))
      password2 = str(escape(request.form.get('password2')))

      user = User.query.filter_by(email=email).first()
      if user:
        flash('Email already exists.', category='error')
      elif len(email) < 4:
        flash('Email must be greater than 4 characters', category='error')
      elif len(firstName) < 2:
        flash('Name must be at least 1 character', category='error')
      elif password1 != password2:
        flash('Passwords do not match', category='error')
      elif len(password1) < 7:
        flash('Password must be at least 7 characters', category='error')
      else:
        new_user = User(email=email, firstName=firstName, password=generate_password_hash(password1, method='sha256'))
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user, remember=True)
        flash('Account Created!', category='success')
        return redirect(url_for('views.home'))

  return render_template("signup.html", user=current_user)