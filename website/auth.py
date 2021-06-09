from flask import Blueprint, render_template, request, flash, redirect, url_for, session, escape
from flask_login import login_user, login_required, logout_user, current_user
import json
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from .views import currency_search
from . import db, mail
from flask_mail import Message


auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
  if current_user.is_authenticated:
    session.pop('_flashes', None)
    return redirect(url_for('views.home'))
  else:
    if 'reset' in session:
      session.pop('reset', None)
    # else:
    #   flash("You must log in to use some features, though you may still search for currencies!", category='error')

  if request.method == 'POST':
    if 'search' in request.form:
      result, bad_query = currency_search(request.form['search'])
      return render_template("login.html", user=current_user, result=result, bad_query=bad_query)

    else:
      email = str(escape(request.form.get('email'))).lower()
      password = str(escape(request.form.get('password')))

      user = User.query.filter_by(email=email).first()
      if user:
        if check_password_hash(user.password, password):
          session.pop('_flashes', None)
          flash('Logged in successfuly!', category='success')
          login_user(user, remember=True)
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
  if current_user.is_authenticated:
    session.pop('_flashes', None)
    return redirect(url_for('views.home'))
  else:
    session.pop('_flashes', None)

  if request.method == 'POST':
    if 'search' in request.form:
      result, bad_query = currency_search(request.form['search'])
      return render_template("login.html", user=current_user, result=result, bad_query=bad_query)

    else:
      email = str(escape(request.form.get('email'))).lower()
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
        user_settings = {
          'timezone':'UTC',
          'displaycurrency':'USD',
          'dashboard': {
            'grid':True,
            'table':False,
            '24hours':True,
            '7days':True,
            '30days':True,
            'quantity':False,
            'netvalue':False
          }
        }
        new_user = User(email=email, firstName=firstName, password=generate_password_hash(password1, method='sha256'), role="basic", 
                        settings=json.dumps(user_settings), value=0, change24h=0, change7d=0, change30d=0)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user, remember=True)
        session.pop('_flashes', None)
        flash('Account Created!', category='success')
        return redirect(url_for('views.home'))

  return render_template("signup.html", user=current_user)


def send_reset_email(user):
  token = user.get_reset_token()
  msg = Message('Password Reset Request',
                sender="noreply@searchcrypto.app",
                recipients=[user.email])
  msg.body= f'''To reset your password, visit the following link:
{url_for('auth.reset_token', token=token, _external=True)}

If you did not make this request, you can ignore this email and no changes will be made.
  '''
  mail.send(msg)


@auth.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
  if current_user.is_authenticated:
    return redirect(url_for('views.home'))

  if request.method == 'POST':
    if 'email' in request.form:
      email = str(escape(request.form.get('email'))).lower()
      user = User.query.filter_by(email=email).first()
      if user:
        send_reset_email(user)
      flash(f'Password reset link sent to {email}.', category='success')
      session['reset'] = True
      return redirect(url_for('auth.login'))
  form = "request"
  return render_template("accountrecovery.html", user=current_user, form=form)


@auth.route('/accountrecovery/<token>', methods=['GET', 'POST'])
def reset_token(token):
  if current_user.is_authenticated:
    return redirect(url_for('views.home'))

  user = User.verify_reset_token(token)
  if not user:
    flash('Invalid or Expired token', category='error')
    return redirect(url_for('auth.reset_request'))
  form = "reset"

  password1 = str(escape(request.form.get('password1')))
  password2 = str(escape(request.form.get('password2')))
  if password1 != password2:
    flash('Passwords do not match', category='error')
  elif len(password1) < 7:
    flash('Password must be at least 7 characters', category='error')
  else:
    hashed_password = generate_password_hash(password1, method='sha256')
    user.password = hashed_password
    db.session.commit()
    login_user(user, remember=True)
    flash('Password Reset!', category='success')
    return redirect(url_for('views.home'))

  return render_template("accountrecovery.html", user=current_user, form=form)