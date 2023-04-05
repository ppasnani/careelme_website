from flask import Flask, request
from flask import render_template, flash
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.app_context().push()

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password123@localhost/careelme_jobs'
app.config['SECRET_KEY'] = "my super secret secret key"

# Initializing the databse
db = SQLAlchemy(app)
class Jobs(db.Model):
      id = db.Column(db.Integer, primary_key=True)
      position = db.Column(db.String(200), nullable=False, unique=True)
      company = db.Column(db.String(200), nullable=False)
      location = db.Column(db.String(200))
      min_salary = db.Column(db.Integer)
      max_salary = db.Column(db.Integer)
      status = db.Column(db.String(200), default="Flagged", nullable=False)

# Create a Form class
class JobForm(FlaskForm):
	# Good schema based on teal website
    # Job position, company, min salary, max salary, location, status, date saved, follow up, excitement    
	job_position = StringField("Job Position:", validators=[DataRequired()])
	company = StringField("Company Name:", validators=[DataRequired()])
	location = StringField("Location")
	min_salary = IntegerField("Minimum Salary")
	max_salary = IntegerField("Maximum Salary")
	status = StringField()
	submit = SubmitField("Submit")	

# Create a route for user forms
@app.route('/job/add', methods=['GET', 'POST'])
def add_job():
	position = None
	form = JobForm()
	if form.validate_on_submit():
		#jop = Jobs()
		# job = Jobs.query.filter_by(email=form.email.data).first()
		# if user is None:
		# 	user = Users(name=form.name.data, email=form.email.data, favorite_color=form.favorite_color.data)
		# 	db.session.add(user)
		# 	db.session.commit()
		# name = form.name.data
		# form.name.data = ''
		# form.email.data = ''
		# form.favorite_color.data = ''
		position = form.job_position.data
		flash(f'User Added Successfully{position}')
	#our_users = Users.query.order_by(Users.date_added)
	return render_template("add_job.html", form=form, job=position)


@app.route('/')
def index():
    return render_template('index.html')