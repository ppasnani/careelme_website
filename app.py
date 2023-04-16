from os import environ as env
from urllib.parse import quote_plus, urlencode

from flask import Flask, request
from flask import render_template, flash, redirect, url_for, session
from flask_wtf import FlaskForm
from dotenv import find_dotenv, load_dotenv

from wtforms import StringField, IntegerField, SubmitField, SelectField, EmailField, PasswordField
from wtforms.validators import DataRequired
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
class Users(db.Model):
		id = db.Column(db.Integer, primary_key=True)
		email = db.Column(db.String(200), nullable=False, unique=True)
		username = db.Column(db.String(200), nullable=False, unique=True)
		date_created = db.Column(db.DateTime, default=datetime.utcnow)
		password_hash = db.Column(db.String(128), nullable=False)

		@property
		def password(self):
			raise AttributeError('password is not a readable attribute')
		
		@password.setter
		def password(self, password):
			self.password_hash = generate_password_hash(password)

		def verify_password(self, password):
			return check_password_hash(self.password_hash, password)

# Create a login form
class LoginForm(FlaskForm):
	#email = StringField("Email", validators=[DataRequired()])
	username = StringField("Username", validators=[DataRequired()])
	password_hash = PasswordField("Password", validators=[DataRequired()])
	submit = SubmitField("Submit")

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

@app.route('/google_authorized')
def google_authorized():
	user_dict = dict(dict(session).get('user', None)['userinfo'])
	# Check if user exists
	user = Users.query.filter_by(username=user_dict['email']).first()
	if user is None:
		user = Users(username=user_dict['nickname'], email=user_dict['email'], password_hash=user_dict['sid'])
		# Add user to database
		db.session.add(user)
		db.session.commit()
	return redirect('/')
	
	#return f"YO YO YO ! Hello user, {user_dict}!"


@app.route('/login', methods=['GET', 'POST'])
def login():
	return oauth.auth0.authorize_redirect(
		redirect_uri=url_for("callback", _external=True)
		)

@app.route('/callback', methods=['GET', 'POST'])
def callback():
	token = oauth.auth0.authorize_access_token()
	session["user"] = token
	return redirect('/google_authorized')

@app.route('/logout')
def logout():
	session.clear()
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
def delete(id):
	job_to_delete = Jobs.query.get_or_404(id)
	try:
		db.session.delete(job_to_delete)
		db.session.commit()
		flash(f'Job Deleted Successfully {job_to_delete.position}')
	except:
		flash(f'Whoops! Delete Failed {job_to_delete.position}')
	return redirect('/')

# Create a route to update job
@app.route('/update/<int:id>', methods=['GET', 'POST'])
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
		return redirect('/')
	else:
		return render_template('update.html', form=form, job_to_update=job_to_update, id=id)

# Create a route to add job
@app.route('/job/add', methods=['GET', 'POST'])
def add_job():
	position = None
	form = JobForm()
	if form.validate_on_submit():
		job = Jobs.query.filter_by(position=form.position.data).first()
		if job is None:
			job = Jobs(position=form.position.data, company=form.company.data, location=form.location.data, min_salary=form.min_salary.data, max_salary=form.max_salary.data, email=form.email.data, status=form.status.data)
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
		return render_template('index.html', our_jobs=our_jobs)
	#our_users = Users.query.order_by(Users.date_added)
	return render_template("add_job.html", form=form, job=position)

@app.route('/')
def index():
    our_jobs = Jobs.query.order_by(Jobs.id)
    our_users = Users.query.order_by(Users.date_created)
    return render_template('index.html', our_jobs=our_jobs, our_users=our_users)