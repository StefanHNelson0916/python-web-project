import os
import secrets
import yaml
from flask_mysqldb import MySQL
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from flaskDemo import app, db, bcrypt
from flaskDemo.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, CreateProjectForm
from flaskDemo.models import User, Post, Bid, Contractor, Contractor_Skills, Customer, Project, Skills, Supplied, Supplier
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, user_type=form.userType.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

#save picture route
def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

#Route to users acccunt
#Renders account.html
@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)

#Route for the customer to create a project
#Uses CreateProjectForm from form.py
#Renders create_project.html
@app.route("/create/project", methods=['GET', 'POST'])
@login_required
def create_project():
    user_type = current_user.user_type
    if user_type == 'Customer':
        form = CreateProjectForm()
        if form.validate_on_submit():
            count = Project.query.count()
            project = Project(projectID = count + 1 ,customerID = current_user.id, projDesc = form.projDesc.data, startDate = form.startDate.data, endDate = form.endDate.data)
            db.session.add(project)
            db.session.commit()
            flash('You have created a new project!','success')
            return redirect(url_for('home'))
        return render_template('create_project.html', title='Create Project', form=form, legend='Create Project')

    else:
        return render_template('unauthorized.html')

#Route for the customer to view their projects
#SQLAlchemy query to find all projects associated with current_user.id
#Renders customer_projects.html
@app.route("/Customer/Projects")
@login_required
def my_projects():
    if current_user.user_type == 'Customer':
        results = Project.query.filter_by(current_user.id)
        return render_template('', results=results)
    else:
        return render_template('unauthorized.html')

#Route for the Customer to see any bids that have been placed on their projects
#SQLAlchemy query to find all the bids on projects that current_user has ongoing
#Renders my_bids.html 
@app.route("/CustomersBids")
@login_required
def CustomersBids():
    if current_user.user_type == 'Customer':
        results = Project.query.filter_by(customerID =current_user.id) \
            .join(Bid,Project.projectID==Bid.projectID) \
                .join(Contractor,Project.contractorID==Contractor.contractorID) \
                    .add_columns(Bid.projectID,Bid.contractorID,Bid.priceDesc,Bid.price,Bid.hours, Contractor.name)
        return render_template('my_bids.html', joined_m_n=results)
    else:
        return render_template('unauthorized.html')

#Route for the contractors to view their projects
#SQLAlchemy query to find all projects associated with current_user.id
#Renders customer_projects.html
@app.route("/Contractor/Projects")
@login_required
def contractors_projects():
    if current_user.user_type == 'Contractor':
        results = Project.query.filter_by(current_user.id)
        return render_template('', results=results)
    else:
        return render_template('unauthorized.html')

@app.route('/test/')
def test():
    return render_template('test.html')
