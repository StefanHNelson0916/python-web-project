import os
import secrets
import yaml
from flask_mysqldb import MySQL
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from flaskDemo import app, db, bcrypt, mysql
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
@app.route("/CustomersProjects")
@login_required
def my_projects():
    if current_user.user_type == 'Customer':
        results = Project.query.filter_by(current_user.id)
        return render_template('', results=results)
    else:
        return render_template('unauthorized.html')

#Route for the Customer to see any bids that have been placed on their projects
#SQLAlchemy query to find all the bids on projects that current_user has ongoing
#Renders customers_bids.html 
@app.route("/CustomersBids")
@login_required
def customers_bids():
    if current_user.user_type == 'Customer':
        results = Project.query.filter_by(customerID =current_user.id) \
            .join(Bid,Project.projectID==Bid.projectID) \
                .join(Contractor,Project.contractorID==Contractor.contractorID) \
                    .add_columns(Bid.projectID,Bid.contractorID,Bid.priceDesc,Bid.price,Bid.hours, Contractor.name)
        return render_template('customers_bids.html', joined_m_n=results)
    else:
        return render_template('unauthorized.html')

#Route for the contractor too see all the skills that are associated with their ID
#Renders contractors_skills_home.html
@app.route("/ContractorSkills")
@login_required
def contractors_skills():
    if current_user.user_type == 'Contractor':
        results = Contractor_Skills.query.filter_by(contractorID = current_user.id) \
            .join(Skills,Contractor_Skills.skillID == Skills.skillID) \
                .add_columns(Skills.skillID,Skills.skillName,Skills.description,Contractor_Skills.yearsExperience,Contractor_Skills.certification,Contractor_Skills.contractorID)
        return render_template('contractor_skills.html', joined_m_n=results)

#Route to delete the selected skill from the contractors account
@app.route("/ContractorSkills/<contractorID>/<skillID>delete", methods=['POST'])
@login_required
def delete_skill(contractorID,skillID):
    contractor_skill = Contractor_Skills.query.get_or_404([contractorID,skillID])
    db.session.delete(contractor_skill)
    db.session.commit()
    flash('Your Skill has been deleted!', 'success')
    return redirect(url_for('contractors_skills'))

#Route to update the selected skill from the contractors account
#Uses form UpdateSkillForm
#Renders update_skill.html
@app.route("/ContractorSkills/<contractorID>/<skillID>update", methods=['GET','POST'])
@login_required
def update_skill(contractorID, skillID):
    form = UpdateSkillForm()
    contractor_skill = Contractor_Skills.query.get_or_404([contractorID, skillID])
    if form.validate_on_submit():
        contractor_skill.skillID = form.skillID.data
        contractor_skill.yearsExperience = form.yearsExperience.data
        contractor_skill.certification = form.certification.data
        db.session.commit()
        flash('Your Skill has been updated!', 'success')
        return redirect(url_for('contractors_skills'))
    return render_template('update_skill.html', title='Update Skill', form=form, contractor_skill=contractor_skill)

@app.route("/AllBids")
@login_required
def all_bids():
    cur = mysql.connection.cursor()
    resultValue = cur.execute("SELECT * FROM project WHERE contractorID IN (SELECT contractorID FROM bid)")
    if resultValue > 0:
        bidResults = cur.fetchall()
        return render_template('all_bids.html', bidResults=bidResults)

@app.route("/SkillsOffered")
@login_required
def skills_offered():
    cur = mysql.connection.cursor()
    resultsValue = cur.execute("SELECT name, address, description, hourlyRate, phoneNumber, skillID, yearsExperience, certification FROM contractor LEFT JOIN contractor_skills ON contractor.contractorID = contractor_skills.contractorID")
    if resultsValue > 0:
        skillsResults = cur.fetchall()
        return render_template('skills_offered.html', skillsResults=skillsResults)

@app.route("/SuppliedInformation")
@login_required
def supplied_information():
    cur = mysql.connection.cursor()
    resultsValue = cur.execute("SELECT MIN(supplyQty) as minSupplyQty, MAX(supplyQty) as maxSupplyQty, AVG(supplyQty) as avgSupplyQty, MIN(supplyPrice) as minSupplyPrice, MAX(supplyPrice) as maxSupplyPrice, AVG(supplyPrice) as avgSupplyPrice FROM supplied; ")
    if resultsValue > 0:
        suppliedInfoResults = cur.fetchall()
        return render_template('supplied_info.html', suppliedInfoResults=suppliedInfoResults)

@app.route("/SuppliedInformation2")
@login_required
def supplied_information2():
    cur = mysql.connection.cursor()
    resultsValue = cur.execute("SELECT * FROM supplied WHERE supplyQty >=5 AND supplyPrice < 10")
    if resultsValue > 0:
        suppliedInfoResults2 = cur.fetchall()
        return render_template('supplied_info2.html', suppliedInfoResults2=suppliedInfoResults2)

@app.route("/ActiveProject")
@login_required
def active_projects():
    results = Project.query.filter_by(contractorID = current_user.id) \
        .filter_by(projStatus = 'Not Done')
    return render_template('active_projects.html',results=results)

