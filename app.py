from sqlalchemy import or_
from flask import Flask, render_template, request, redirect, url_for, flash, session
from Model.model import *
from sqlalchemy.exc import IntegrityError
from datetime import datetime


app = Flask(__name__)
app.config['SECRET_KEY'] = 'East'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///grocery.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_SILENCE_UBER_WARNING'] = 1

db.init_app(app)


with app.app_context():
    db.create_all()

#------------------------------------ Login Logout and Signup form-------------------------------------#

@app.route("/", methods=["GET"])
def home():
    return redirect (url_for('logout'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']  # Get the role from the form

        try:
            user = User(username=username, email=email, password=password, role=role)
            db.session.add(user)
            db.session.commit()

            flash('Your account was created successfully.', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            flash('Username or email already exists. Please choose a different one.', 'danger')
            return redirect(url_for('signup'))

    return render_template('signup.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form['username']
        password = request.form['password']

        user = User.query.filter(
            or_(User.username == username_or_email, User.email == username_or_email)).first()

        if user and user.password == password:
            session['user_id'] = user.id
            session['role'] = user.role

            # Redirect based on role
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard', curr_login_id=user.id))  # Pass curr_login_id here
            elif user.role == 'professional':
                return redirect(url_for('professional_dashboard',curr_login_id=user.id))
            else:
                return redirect(url_for('customer_dashboard',curr_login_id=user.id))
        else:
            flash('Invalid Username or Password', 'danger')
            return render_template('login.html')

    return render_template('login.html')


#---------------------------------------- Admin Dashboard----------------------------------------------#


@app.route('/admin_dashboard/<int:curr_login_id>', methods=['GET'])
def admin_dashboard(curr_login_id):
    user = User.query.get(curr_login_id)
    if not user or user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('logout'))

    # Fetch customers and professionals
    customers = User.query.filter_by(role='customer').all()
    professionals = User.query.filter_by(role='professional').all()

    # Fetch services
    services = Service.query.all()

    data = {'curr_login_id': curr_login_id}
    return render_template('admin_dashboard.html', 
                        name=user.username, 
                        curr_login_id=curr_login_id, 
                        customers=customers, 
                        professionals=professionals, 
                        services=services,
                        data=data)

@app.route('/admin/stats/<int:curr_login_id>', methods=['GET'])
def admin_stats(curr_login_id):
    # Your logic for the admin_stats view
    return render_template('admin_stats.html', curr_login_id=curr_login_id)


@app.route('/create_service/<int:curr_login_id>', methods=['GET', 'POST'])
def create_service(curr_login_id):
    admin_user = User.query.get(curr_login_id)
    if not admin_user or admin_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('logout'))

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        description = request.form['description']

        new_service = Service(name=name, price=price, description=description)
        db.session.add(new_service)
        db.session.commit()

        flash('New service created successfully!', 'success')
        return redirect(url_for('admin_dashboard', curr_login_id=curr_login_id))

    return render_template('create_service.html', curr_login_id=curr_login_id)

    
@app.route('/delete_service/<int:curr_login_id>/<int:service_id>', methods=['GET'])
def delete_service(curr_login_id, service_id):
    admin_user = User.query.get(curr_login_id)
    if not admin_user or admin_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('logout'))

    service = Service.query.get(service_id)
    if service:
        db.session.delete(service)
        db.session.commit()
        flash('Service deleted successfully!', 'success')
    else:
        flash('Service not found.', 'danger')

    return redirect(url_for('admin_dashboard', curr_login_id=curr_login_id))

@app.route('/edit_service/<int:curr_login_id>/<int:service_id>', methods=['GET', 'POST'])
def edit_service(curr_login_id, service_id):
    admin_user = User.query.get(curr_login_id)
    if not admin_user or admin_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('logout'))

    service = Service.query.get(service_id)
    if not service:
        flash('Service not found.', 'danger')
        return redirect(url_for('admin_dashboard', curr_login_id=curr_login_id))

    if request.method == 'POST':
        service.name = request.form['name']
        service.price = request.form['price']
        service.description = request.form['description']
        db.session.commit()

        flash('Service updated successfully!', 'success')
        return redirect(url_for('admin_dashboard', curr_login_id=curr_login_id))

    return render_template('edit_service.html', service=service, curr_login_id=curr_login_id)


@app.route('/approve_professional/<int:curr_login_id>/<int:user_id>', methods=['GET'])
def approve_professional(curr_login_id, user_id):
    admin_user = User.query.get(curr_login_id)
    if not admin_user or admin_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('logout'))

    professional = User.query.get(user_id)
    if professional and professional.role == 'professional':
        professional.status = 'approved'
        db.session.commit()
        flash('Service professional approved.', 'success')
    else:
        flash('Service professional not found or invalid role.', 'danger')

    return redirect(url_for('admin_dashboard', curr_login_id=curr_login_id))



@app.route('/disapprove_professional/<int:curr_login_id>/<int:user_id>', methods=['GET'])
def disapprove_professional(curr_login_id, user_id):
    user = User.query.get(curr_login_id)
    if not user or user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('logout'))

    professional = User.query.get(user_id)
    if professional and professional.role == 'professional':
        professional.status = 'disapproved'
        db.session.commit()
        flash('Service professional disapproved.', 'danger')
    else:
        flash('Professional not found or invalid role.', 'danger')

    return redirect(url_for('admin_dashboard', curr_login_id=user.id))


# --------------------------------------- Customer Section ----------------------------------------- #

@app.route('/customer_dashboard/<int:curr_login_id>', methods=['GET'])
def customer_dashboard(curr_login_id):
    user = User.query.get(curr_login_id)
    if not user or user.role != 'customer':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('logout'))
    
    # Fetch all available services for the customer
    services = Service.query.all()
    # Fetch all service requests related to the current customer, including their current status
    service_requests = ServiceRequest.query.filter_by(customer_id=curr_login_id).all()

    return render_template('customer_dashboard.html',
                           user=user, 
                           services=services, 
                           service_requests=service_requests, 
                           curr_login_id=curr_login_id)

@app.route('/search_services/<int:curr_login_id>', methods=['POST'])
def search_services(curr_login_id):
    user = User.query.get(curr_login_id)
    if not user or user.role != 'customer':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('logout'))
    
    search_query = request.form['search_query']
    services = Service.query.filter(
        or_(
            Service.name.ilike(f'%{search_query}%'),
            Service.description.ilike(f'%{search_query}%')
        )
    ).all()

    return render_template('search_services.html', 
                           curr_login_id=curr_login_id, 
                           services=services, 
                           query=search_query)

@app.route('/create_service_request/<int:curr_login_id>/<int:service_id>', methods=['GET', 'POST'])
def create_service_request(curr_login_id, service_id):
    customer = User.query.get(curr_login_id)
    if not customer or customer.role != 'customer':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('logout'))
    
    if request.method == 'POST':
        remarks = request.form['remarks']
        service_request = ServiceRequest(
            customer_id=curr_login_id,
            service_id=service_id,
            status='requested',
            remarks=remarks,
            date_of_request=datetime.now()
        )
        db.session.add(service_request)
        db.session.commit()
        flash('Service request created successfully!', 'success')
        return redirect(url_for('customer_dashboard', curr_login_id=curr_login_id))

    service = Service.query.get(service_id)
    return render_template('create_service_request.html', 
                           service=service, 
                           curr_login_id=curr_login_id)

@app.route('/close_service_request/<int:curr_login_id>/<int:request_id>', methods=['GET', 'POST'])
def close_service_request(curr_login_id, request_id):
    customer = User.query.get(curr_login_id)
    if not customer or customer.role != 'customer':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('logout'))

    service_request = ServiceRequest.query.get(request_id)
    if not service_request or service_request.customer_id != curr_login_id or service_request.status != 'completed':
        flash('Service request not found or cannot be closed.', 'danger')
        return redirect(url_for('customer_dashboard', curr_login_id=curr_login_id))

    if request.method == 'POST':
        # Capture remark and rating
        remark = request.form.get('remark')
        rating = int(request.form.get('rating', 0))  # Ensure rating is numeric

        # Validate the rating
        if rating < 1 or rating > 5:
            flash('Rating must be between 1 and 5.', 'danger')
            return redirect(url_for('close_service_request', curr_login_id=curr_login_id, request_id=request_id))

        # Update the service request with remark, rating, and status
        service_request.status = 'closed'
        service_request.remark = remark
        service_request.rating = rating
        db.session.commit()
        flash('Service request closed successfully with feedback!', 'success')
        return redirect(url_for('customer_dashboard', curr_login_id=curr_login_id))

    # Render the close service request form
    return render_template('close_service_request.html', service_request=service_request, curr_login_id=curr_login_id)





# -------------------------------- Service Professional Section -------------------------------- #

@app.route('/professional_dashboard/<int:curr_login_id>', methods=['GET'])
def professional_dashboard(curr_login_id):
    # Fetch the professional user
    professional = User.query.get(curr_login_id)
    if not professional or professional.role != 'professional':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('logout'))

    # Fetch service requests
    open_requests = ServiceRequest.query.filter_by(status='requested').all()
    assigned_requests = ServiceRequest.query.filter_by(status='assigned', professional_id=curr_login_id).all()
    closed_requests = ServiceRequest.query.filter_by(status='closed', professional_id=curr_login_id).all()

    # Pass the professional object to the template
    return render_template('professional_dashboard.html',
                           professional=professional,
                           open_requests=open_requests,
                           assigned_requests=assigned_requests,
                           closed_requests=closed_requests,
                           curr_login_id=curr_login_id)



@app.route('/accept_service_request/<int:curr_login_id>/<int:request_id>', methods=['POST'])
def accept_service_request(curr_login_id, request_id):
    professional = User.query.get(curr_login_id)
    if not professional or professional.role != 'professional':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('logout'))

    service_request = ServiceRequest.query.get(request_id)
    if service_request and service_request.status == 'requested':
        # Assign the service request to the logged-in professional
        service_request.professional_id = curr_login_id
        service_request.status = 'assigned'
        db.session.commit()
        flash('Service request accepted successfully!', 'success')
    else:
        flash('Service request not found or already assigned.', 'danger')

    # Redirect back to the professional dashboard instead of a separate service request view page
    return redirect(url_for('professional_dashboard', curr_login_id=curr_login_id))

@app.route('/mark_service_completed/<int:curr_login_id>/<int:request_id>', methods=['POST'])
def mark_service_completed(curr_login_id, request_id):
    professional = User.query.get(curr_login_id)
    if not professional or professional.role != 'professional':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('logout'))

    service_request = ServiceRequest.query.get(request_id)
    if service_request and service_request.status == 'assigned' and service_request.professional_id == curr_login_id:
        # Update the status of the service request to 'completed'
        service_request.status = 'completed'
        service_request.date_of_completion = datetime.now()
        db.session.commit()
        flash('Service marked as completed successfully!', 'success')
    else:
        flash('Service request not found or cannot be marked as completed.', 'danger')

    # Redirect back to the professional dashboard
    return redirect(url_for('professional_dashboard', curr_login_id=curr_login_id))







@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__=="__main__":
    app.run(port=5500,debug=True)




