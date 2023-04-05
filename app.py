from flask import Flask, request
from flask import render_template, flash
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, SelectField
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
      #date_added = db.Column(db.DateTime, default=datetime.utcnow)
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
	position = StringField("Job Position:", validators=[DataRequired()])
	company = StringField("Company Name:", validators=[DataRequired()])
	location = StringField("Location")
	min_salary = IntegerField("Minimum Salary")
	max_salary = IntegerField("Maximum Salary")
	#    color = SelectField('Select a color', choices=[('red', 'Red'), ('green', 'Green'), ('blue', 'Blue')])
	status = SelectField('Status', choices=[('Flagged', 'Flagged'), ('Applied', 'Applied'), ('Interview', 'Interview'), ('Offer', 'Offer'), ('Rejected', 'Rejected')])
	submit = SubmitField("Submit")	

# Create a route for user forms
@app.route('/job/add', methods=['GET', 'POST'])
def add_job():
	position = None
	form = JobForm()
	if form.validate_on_submit():
		job = Jobs.query.filter_by(position=form.position.data).first()
		if job is None:
			job = Jobs(position=form.position.data, company=form.company.data, location=form.location.data, min_salary=form.min_salary.data, max_salary=form.max_salary.data, status=form.status.data)
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
		#position = form.position.data
		flash(f'User Added Successfully {position}')
		our_jobs = Jobs.query.order_by(Jobs.id)
		return render_template('index.html', our_jobs=our_jobs)
	#our_users = Users.query.order_by(Users.date_added)
	return render_template("add_job.html", form=form, job=position)

@app.route('/')
def index():
    our_jobs = Jobs.query.order_by(Jobs.id)
    return render_template('index.html', our_jobs=our_jobs)