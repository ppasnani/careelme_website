from os import environ as env
from urllib.parse import quote_plus, urlencode

from flask import Flask, request
from flask import render_template, flash, redirect, url_for, session
from flask_wtf import FlaskForm
from dotenv import find_dotenv, load_dotenv
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
import mailtrap as mt

from wtforms import StringField, IntegerField, SubmitField, SelectField, EmailField
from wtforms.validators import DataRequired
from wtforms.widgets import TextArea
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash

from authlib.integrations.flask_client import OAuth

ENV_FILE = find_dotenv()
if ENV_FILE:
	load_dotenv(ENV_FILE)

app = Flask(__name__)
app.app_context().push()

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password123@localhost/careelme_jobs'
app.secret_key = env.get("APP_SECRET_KEY")

#app.config['MAIL_SERVER']='sandbox.smtp.mailtrap.io'
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = env.get("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = env.get("MAIL_PASSWORD")
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
# Configure flask app to be testing
#app.config['TESTING'] = True

mail = Mail(app)

# Setting up 0Auth stuff
oauth = OAuth(app)
oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)

# Initializing the databse
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# User class
class Users(db.Model, UserMixin):
		id = db.Column(db.Integer, primary_key=True)
		email = db.Column(db.String(200), nullable=False, unique=True)
		username = db.Column(db.String(200), nullable=False, unique=True)
		date_created = db.Column(db.DateTime, default=datetime.utcnow)
		password_hash = db.Column(db.String(128), nullable=False)
		# A user can have many jobs
		jobs = db.relationship('Jobs', backref='poster')

		@property
		def password(self):
			raise AttributeError('password is not a readable attribute')
		
		@password.setter
		def password(self, password):
			self.password_hash = generate_password_hash(password)

		def verify_password(self, password):
			return check_password_hash(self.password_hash, password)

# Job class
class Jobs(db.Model):
		id = db.Column(db.Integer, primary_key=True)
		date = db.Column(db.DateTime, default=datetime.utcnow)
		position = db.Column(db.String(200), nullable=False, unique=True)
		company = db.Column(db.String(200), nullable=False)
		location = db.Column(db.String(200))
		min_salary = db.Column(db.Integer)
		max_salary = db.Column(db.Integer)
		email = db.Column(db.String(200), nullable=False)
		status = db.Column(db.String(200), default="Flagged", nullable=False)
		# Foreign key to link Users (refers to the primary key of the Users)
		# A job only has one user
		poster_id = db.Column(db.Integer, db.ForeignKey('users.id'))

# Create a Form class
class JobForm(FlaskForm):
	# Good schema based on teal website
    # Job position, company, min salary, max salary, location, status, date saved, follow up, excitement    
	position = StringField("Job Position:", validators=[DataRequired()])
	company = StringField("Company Name:", validators=[DataRequired()])
	location = StringField("Location")
	min_salary = IntegerField("Minimum Salary")
	max_salary = IntegerField("Maximum Salary")
	status = SelectField('Status', choices=[('Flagged', 'Flagged'), ('Applied', 'Applied'), ('Interview', 'Interview'), ('Offer', 'Offer'), ('Rejected', 'Rejected')])
	email = EmailField("Email Address", validators=[DataRequired()])
	submit = SubmitField("Submit")	

# Create a form for the email to be sent
class EmailForm(FlaskForm):
	subject = StringField("Subject", validators=[DataRequired()])
	body = StringField("Body", validators=[DataRequired()], widget=TextArea())
	submit = SubmitField("Submit")

# Flask login stuff
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
	return Users.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
	return oauth.auth0.authorize_redirect(
		redirect_uri=url_for("callback", _external=True)
		)

@app.route('/callback', methods=['GET', 'POST'])
def callback():
	token = oauth.auth0.authorize_access_token()
	session["user"] = token
	return redirect('/authorized')

@app.route('/authorized')
def authorized():
	user_dict = dict(dict(session).get('user', None)['userinfo'])
	# Check if user exists
	user = Users.query.filter_by(email=user_dict['email']).first()
	if user is None:
		# Create a new user
		user = Users(username=user_dict['nickname'], email=user_dict['email'], password_hash=user_dict['sid'])
		# Add user to database
		db.session.add(user)
		db.session.commit()
	login_user(user)
	return redirect('/dashboard')

@app.route('/logout')
@login_required
def logout():
	session.clear()
	logout_user()
	return redirect(
        "https://" + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("index", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

# Create a route to delete a user
@app.route('/delete_user/<int:id>')
def delete_user(id):
	user_to_delete = Users.query.get_or_404(id)
	try:
		db.session.delete(user_to_delete)
		db.session.commit()
		flash(f'User Deleted Successfully {user_to_delete.username}')
	except:
		flash(f'Whoops! Delete Failed {user_to_delete.username}')
	return redirect('/')

# Create a route to delete job
@app.route('/delete/<int:id>')
@login_required
def delete(id):
	job_to_delete = Jobs.query.get_or_404(id)
	try:
		db.session.delete(job_to_delete)
		db.session.commit()
		flash(f'Job Deleted Successfully {job_to_delete.position}')
	except:
		flash(f'Whoops! Delete Failed {job_to_delete.position}')
	return redirect('/dashboard')

# Create a route to update job
@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
	job_to_update = Jobs.query.get_or_404(id)
	# Critical to load form after getting the job
	# This allows me to set the value of the select field as the form loads
	form=JobForm(status=job_to_update.status)
	if request.method == 'POST':
		job_to_update.position = request.form['position']
		job_to_update.company = request.form['company']
		job_to_update.status = request.form['status']
		job_to_update.email = request.form['email']
		
		try:
			db.session.commit()
			flash(f'Job Updated Successfully {job_to_update.position}')
		except:
			flash(f'Job Update Failed {job_to_update.position}')
		return redirect('/dashboard')
	else:
		return render_template('update.html', form=form, job_to_update=job_to_update, id=id)

# Create a route to add job
@app.route('/job/add', methods=['GET', 'POST'])
@login_required
def add_job():
	position = None
	form = JobForm()
	if form.validate_on_submit():
		# Poster doesnt work right now since we don't have a login session. Coming back to this
		poster = current_user.id
		job = Jobs.query.filter_by(position=form.position.data).first()
		if job is None:
			job = Jobs(position=form.position.data, company=form.company.data, 
	      	location=form.location.data, min_salary=form.min_salary.data, max_salary=form.max_salary.data, 
			email=form.email.data, status=form.status.data, poster_id=poster)
			db.session.add(job)
			db.session.commit()
		# Save the position for display
		position=form.position.data
		# Clear the form
		form.position.data = ''
		form.company.data = ''
		form.location.data = ''
		form.min_salary.data = ''
		form.max_salary.data = ''
		form.status.data = ''
		flash(f'Job Added Successfully {position}')
		our_jobs = Jobs.query.order_by(Jobs.id)
		return redirect('/dashboard')
	
	return render_template("add_job.html", form=form, job=position)

# Create a route to send an email to the job contact
@app.route('/send_email/<int:id>', methods=['GET', 'POST'])
@login_required
def send_email(id):
	job_to_email = Jobs.query.get_or_404(id)
	form = EmailForm()
	if form.validate_on_submit():
		# Send email
		msg = Message(form.subject.data, 
			sender=current_user.email, 
			recipients=[job_to_email.email], 
			extra_headers={'Disposition-Notification-To': current_user.email})
		msg.body = form.body.data
		mail.send(msg)
		flash(f'Email Sent Successfully to {job_to_email.email}')
		return redirect('/dashboard')
	return render_template('send_email.html', form=form, job_to_email=job_to_email)

# Createa a dashboard page
@app.route('/dashboard')
@login_required
def dashboard():
	# Only query the jobs associated with the current user
	our_jobs = Jobs.query.filter_by(poster_id=current_user.id).order_by(Jobs.id)
	return render_template('dashboard.html', our_jobs=our_jobs)

@app.route('/')
def index():
    our_jobs = Jobs.query.order_by(Jobs.id)
    our_users = Users.query.order_by(Users.date_created)
    return render_template('index.html', our_jobs=our_jobs, our_users=our_users)