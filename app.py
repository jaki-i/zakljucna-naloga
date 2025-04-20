from flask import Flask, render_template, url_for, redirect, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from flask import flash
import os
from datetime import datetime
from werkzeug.utils import secure_filename
#pip install flask, flask_sqlalchemy, flask_login, flask_wtf, wtforms, wtforms.validators, flask_bcrypt, os, datetime, secure_filename

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_IMAGE_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['ALLOWED_VIDEO_EXTENSIONS'] = {'mp4', 'mov', 'avi', 'webm'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
db = SQLAlchemy(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'images'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'videos'), exist_ok=True)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

carmeet_participants = db.Table('carmeet_participants',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('carmeet_id', db.Integer, db.ForeignKey('carmeet.id'), primary_key=True)
)

race_participants = db.Table('race_participants',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('race_id', db.Integer, db.ForeignKey('race.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    car = db.Column(db.String(20), nullable=True)
    car_description = db.Column(db.Text, nullable=True)
    password = db.Column(db.String(80), nullable=False)

class Carmeet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    start_time = db.Column(db.String(20), nullable=False)
    end_time = db.Column(db.String(20), nullable=False)
    car_entry_fee = db.Column(db.Boolean, default=False)
    visitor_ticket = db.Column(db.Boolean, default=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    participants = db.relationship('User', secondary=carmeet_participants,
                                  backref=db.backref('carmeets', lazy='dynamic'))

class Race(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    car_name = db.Column(db.String(20), nullable=False)
    hp = db.Column(db.String(4), nullable=False)
    mods = db.Column(db.String(20), nullable=True)
    participants_limit = db.Column(db.Integer)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    participants = db.relationship('User', secondary=race_participants,
                                  backref=db.backref('races', lazy='dynamic'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class RegisterForm(FlaskForm):
    username = StringField(validators=[
        InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    car = StringField(validators=[
        Length(max=50)], render_kw={"placeholder": "Car (optional)"})
    car_description = StringField(validators=[
        Length(max=50)], render_kw={"placeholder": "Description (mods)"})
    password = PasswordField(validators=[
         InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError('That username already exists. Please choose a different one.')

class LoginForm(FlaskForm):
    username = StringField(validators=[
        InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[
        InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Login')

class AccountForm(FlaskForm):
    username = StringField(validators=[
        Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    car = StringField(validators=[
        Length(max=50)], render_kw={"placeholder": "Car"})
    car_description = StringField(validators=[
        Length(max=200)], render_kw={"placeholder": "Mods description"})
    old_password = PasswordField(render_kw={"placeholder": "Old password"})
    new_password = PasswordField(validators=[
        Length(min=4, max=20)], render_kw={"placeholder": "New password"})
    submit = SubmitField('Update Account')

class CarmeetForm(FlaskForm):
    name = StringField(validators=[
        InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Name"})
    start = StringField(validators=[
        InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Start time"})
    end = StringField(validators=[
        InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "End time"})
    centry = StringField(validators=[
        Length(max=50)], render_kw={"placeholder": "Car entry fee"})
    ventry = StringField(validators=[
        Length(max=50)], render_kw={"placeholder": "Visitor entry fee"})
    submit = SubmitField('Create car meet')

class RaceForm(FlaskForm):
    name = StringField(validators=[
        InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Name"})
    car_name = StringField(validators=[
        InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Car"})
    hp = StringField(validators=[
        InputRequired(), Length(min=2, max=4)], render_kw={"placeholder": "Horsepower"})
    mods = StringField(validators=[
        Length(min=4, max=50)], render_kw={"placeholder": "Modifications"})
    participants_limit = StringField(validators=[
        InputRequired(), Length(max=2)], 
        render_kw={"placeholder": "Number of participants (2-8)"})
    submit = SubmitField('Create race')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, 
                        password=hashed_password, 
                        car=form.car.data if form.car.data else None)  
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/glavna')
def glavna():
    carmeets = Carmeet.query.all()
    races = Race.query.all()
    return render_template('glavna.html', carmeets=carmeets, races=races)

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = AccountForm()
    if form.validate_on_submit():
        try:
            # updata username ce je na novo upisan in ni enak prejsnemu
            if form.username.data and form.username.data != current_user.username:
                # pregleda ce username ze obstaja
                existing_user = User.query.filter_by(username=form.username.data).first()
                if existing_user and existing_user.id != current_user.id:
                    flash('Username already exists', 'error')
                    return render_template('account.html', form=form)
                current_user.username = form.username.data
            
            # updata car and car description
            current_user.car = form.car.data
            current_user.car_description = form.car_description.data
            
            # updata password ce sta star in nov podana
            if form.old_password.data and form.new_password.data:
                if bcrypt.check_password_hash(current_user.password, form.old_password.data):
                    hashed_password = bcrypt.generate_password_hash(form.new_password.data)
                    current_user.password = hashed_password
                else:
                    flash('Old password is incorrect', 'error')
                    return render_template('account.html', form=form)
            
            # commita change na database.db
            db.session.commit()
            flash('Account successfully updated', 'success')
            return redirect(url_for('account'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating account: {str(e)}', 'error')
    
    # Pre-fill form with current user data
    if request.method == 'GET':
        form.username.data = current_user.username
        form.car.data = current_user.car
        form.car_description.data = current_user.car_description
    
    return render_template('account.html', form=form)

@app.route('/carmeet', methods=['GET', 'POST'])
@login_required
def carmeet():
    form = CarmeetForm()
    
    if form.validate_on_submit():
            latitude = float(request.form.get('latitude'))
            longitude = float(request.form.get('longitude'))
            
            if not latitude or not longitude:
                flash('Please select a location on the map', 'error')
                return render_template('carmeet.html', form=form)
            
            new_carmeet = Carmeet(
                name=form.name.data,
                latitude=latitude, 
                longitude=longitude,
                start_time=form.start.data,
                end_time=form.end.data,
                car_entry_fee=bool(form.centry.data),
                visitor_ticket=bool(form.ventry.data),
                creator_id=current_user.id
            )
            
            db.session.add(new_carmeet)
            db.session.commit()
            flash('Car meet created successfully!', 'success')
            return redirect(url_for('glavna'))
    
    return render_template('carmeet.html', form=form)

@app.route('/join_carmeet/<int:carmeet_id>', methods=['POST'])
@login_required
def join_carmeet(carmeet_id):
    carmeet = Carmeet.query.get_or_404(carmeet_id)
    
    if current_user not in carmeet.participants:
        carmeet.participants.append(current_user)
        db.session.commit()
        flash('You have joined the car meet!', 'success')
    else:
        flash('You are already participating in this car meet', 'info')
    
    return redirect(url_for('glavna'))

@app.route('/leave_carmeet/<int:carmeet_id>', methods=['POST'])
@login_required
def leave_carmeet(carmeet_id):
    carmeet = Carmeet.query.get_or_404(carmeet_id)
    
    if current_user in carmeet.participants:
        carmeet.participants.remove(current_user)
        db.session.commit()
        flash('You have left the car meet', 'success')
    else:
        flash('You are not participating in this car meet', 'info')
    
    return redirect(url_for('glavna'))

@app.route('/delete_carmeet/<int:carmeet_id>', methods=['POST'])
@login_required
def delete_carmeet(carmeet_id):
    carmeet = Carmeet.query.get_or_404(carmeet_id)

    if carmeet.creator_id == current_user.id:
        try:
            db.session.delete(carmeet)
            db.session.commit()
            flash('Car meet deleted successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting car meet: {str(e)}', 'error')
    else:
        flash('You can only delete car meets that you created', 'error')
    
    return redirect(url_for('glavna'))

@app.route('/race', methods=['GET', 'POST'])
@login_required
def race():
    form = RaceForm()
    
    if form.validate_on_submit():
            latitude = float(request.form.get('latitude'))
            longitude = float(request.form.get('longitude'))

            if not latitude or not longitude:
                flash('Please select a location on the map', 'error')
                return render_template('race.html', form=form)
            
            new_race = Race(
                name=form.name.data,
                latitude=latitude, 
                longitude=longitude,
                car_name=form.car_name.data,
                hp=form.hp.data,
                mods=form.mods.data,
                participants_limit=int(form.participants_limit.data),
                creator_id=current_user.id
            )

            new_race.participants.append(current_user)

            db.session.add(new_race)
            db.session.commit()
            flash('Race created successfully!', 'success')
            return redirect(url_for('glavna'))        

    return render_template('race.html', form=form)

@app.route('/join_race/<int:race_id>', methods=['POST'])
@login_required
def join_race(race_id):
    race = Race.query.get_or_404(race_id)
    
    if len(race.participants) >= race.participants_limit:
        flash('This race has reached its participant limit', 'error')
        return redirect(url_for('glavna'))
    
    if current_user not in race.participants:
        race.participants.append(current_user)
        db.session.commit()
        flash('You have joined the race!', 'success')
    else:
        flash('You are already participating in this race', 'info')
    
    return redirect(url_for('glavna'))

@app.route('/leave_race/<int:race_id>', methods=['POST'])
@login_required
def leave_race(race_id):
    race = Race.query.get_or_404(race_id)
    
    if current_user in race.participants:
        race.participants.remove(current_user)
        db.session.commit()
        flash('You have left the car meet', 'success')
    else:
        flash('You are not participating in this car meet', 'info')
    
    return redirect(url_for('glavna'))

@app.route('/delete_race/<int:race_id>', methods=['POST'])
@login_required
def delete_race(race_id):
    race = Race.query.get_or_404(race_id)

    if race.creator_id == current_user.id:
        try:
            db.session.delete(race)
            db.session.commit()
            flash('Race deleted successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting race: {str(e)}', 'error')
    else:
        flash('You can only delete car meets that you created', 'error')
    
    return redirect(url_for('glavna'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)