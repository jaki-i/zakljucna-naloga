from flask import Flask, render_template, url_for, redirect, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
#pip install flask, flask_sqlalchemy, flask_login, flask_wtf, wtforms, wtforms.validators, flask_bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    car = db.Column(db.String(20), nullable=True)
    car_description = db.Column(db.Text, nullable=True)
    password = db.Column(db.String(80), nullable=False)

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
            flash(
                'That username already exists. Please choose a different one.')

class LoginForm(FlaskForm):
    username = StringField(validators=[
        InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[
        InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Login')

class AccountForm(FlaskForm):
    username = StringField('Username', validators=[Length(min=4, max=20)])
    car = StringField('Car', validators=[Length(max=50)])
    car_description = StringField('Mods description', validators=[Length(max=200)])
    old_password = PasswordField('Old password')
    new_password = PasswordField('New password', validators=[Length(min=4, max=20)])
    submit = SubmitField('Update Account')

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
    return render_template('glavna.html')

from flask import flash

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

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)