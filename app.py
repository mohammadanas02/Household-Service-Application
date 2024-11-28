from sqlalchemy import or_
from flask import Flask, render_template, request, redirect, url_for, flash, session
from Model.model import *
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import io
import base64
from flask import Response


app = Flask(__name__)
app.config['SECRET_KEY'] = 'East'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///householdservice.sqlite3'
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
        role = request.form['role']  

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

        if user:
            if user.blocked:  # We are Checking if the user is blocked.
                flash('You have been blocked!', 'Contact Admin.')
                return render_template('login.html')
            elif user.password == password:
                session['user_id'] = user.id
                session['role'] = user.role

                # Redirectig based on role of the user.
                if user.role == 'admin':
                    return redirect(url_for('admin_dashboard', curr_login_id=user.id))  
                elif user.role == 'professional':
                    return redirect(url_for('professional_dashboard', curr_login_id=user.id))
                else:
                    return redirect(url_for('customer_dashboard', curr_login_id=user.id))
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

    # Fetching all customers and professionals fron the database by their filtering the roles.
    customers = User.query.filter_by(role='customer').all()
    professionals = User.query.filter_by(role='professional').all()

    # Fetching all the services.
    services = Service.query.all()

    data = {'curr_login_id': curr_login_id}
    return render_template('admin_dashboard.html', 
                        name=user.username, 
                        curr_login_id=curr_login_id, 
                        customers=customers, 
                        professionals=professionals, 
                        services=services,
                        data=data)



@app.route('/admin_dashboard/admin/stats/<int:curr_login_id>', methods=['GET'])
def admin_stats(curr_login_id):
    # Cheaking if the logged in user is admin. 
    admin_user = User.query.get(curr_login_id)
    if not admin_user or admin_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('logout'))

    # Fetching services
    services = Service.query.all()

    # Data preparation for bar graph
    service_names = [service.name for service in services]
    prices = [service.price for service in services]

    # Create a column graph (vertical bars)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(service_names, prices, color='skyblue')
    ax.set_xlabel('Service Name')
    ax.set_ylabel('Price')
    ax.set_title('Price vs Service Name')

    # Rotate x-axis labels for readability
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # Save the plot to a BytesIO object to render it in the HTML
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    # Encode the image to a base64 string
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')

    # Pass the plot_url to the template
    return render_template('admin_stats.html', plot_url=plot_url)


@app.route('/admin_dashboard/create_service/<int:curr_login_id>', methods=['GET', 'POST'])
def create_service(curr_login_id):
    admin_user = User.query.get(curr_login_id)
    if not admin_user or admin_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('logout'))

    if request.method == 'POST':
        name = request.form['name'] # Taking fields from service request form.
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

@app.route('/admin_dashboard/edit_service/<int:curr_login_id>/<int:service_id>', methods=['GET', 'POST'])
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
        service.name = request.form['name'] # reinstantiating fields fron edit page.
        service.price = request.form['price']
        service.description = request.form['description']
        db.session.commit()

        flash('Service updated successfully!', 'success')
        return redirect(url_for('admin_dashboard', curr_login_id=curr_login_id))

    return render_template('edit_service.html', service=service, curr_login_id=curr_login_id)

@app.route('/block_user/<int:curr_login_id>/<int:user_id>', methods=['POST'])
def block_user(curr_login_id, user_id):
    admin_user = User.query.get(curr_login_id)
    if not admin_user or admin_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('logout'))

    user = User.query.get(user_id)
    if user and not user.blocked:
        user.blocked = True
        db.session.commit()
        flash(f'You have blocked {user.username}')
    else:
        flash('User is not found or already blocked!')

    return redirect(url_for('admin_dashboard', curr_login_id=curr_login_id))

@app.route('/unblock_user/<int:curr_login_id>/<int:user_id>', methods=['POST'])
def unblock_user(curr_login_id, user_id):
    admin_user = User.query.get(curr_login_id)
    if not admin_user or admin_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('logout'))

    user = User.query.get(user_id)
    if user and user.blocked:
        user.blocked = False
        db.session.commit()
        flash(f'You have Unblocked {user.username}')
    else:
        flash('User is not found or already blocked!')

    return redirect(url_for('admin_dashboard', curr_login_id=curr_login_id))



# --------------------------------------- Customer Section ----------------------------------------- #

@app.route('/customer_dashboard/<int:curr_login_id>', methods=['GET'])
def customer_dashboard(curr_login_id):
    customer = User.query.get(curr_login_id)
    if not customer or customer.role != 'customer' or customer.blocked:
        flash('Unauthorized access or You have been blocked by the admin')
        return redirect(url_for('logout'))
    
    # Fetching all available services craeted by admin for the customer.
    services = Service.query.all()
    # Fetch all service requests related to the current customer, including their current status.
    service_requests = ServiceRequest.query.filter_by(customer_id=curr_login_id).all()

    return render_template('customer_dashboard.html',
                           customer=customer, 
                           services=services, 
                           service_requests=service_requests, 
                           curr_login_id=curr_login_id)

@app.route('/customer_dashboard/search_services/<int:curr_login_id>', methods=['POST'])
def search_services(curr_login_id):
    customer = User.query.get(curr_login_id)
    if not customer or customer.role != 'customer' or customer.blocked:
        flash('Unauthorized access or You have been blocked by the admin')
        return redirect(url_for('logout'))
    
    search_query = request.form['search_query']
    # Search on the basis of service name or description.
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

@app.route('/customer_dashboard/create_service_request/<int:curr_login_id>/<int:service_id>', methods=['GET', 'POST'])
def create_service_request(curr_login_id, service_id):
    customer = User.query.get(curr_login_id)
    if not customer or customer.role != 'customer' or customer.blocked:
        flash('Unauthorized access or You have been blocked by the admin')
        return redirect(url_for('logout'))
    
    # Taking remarks for the requested service and contact number of the customer.
    if request.method == 'POST':
        remarks = request.form['remarks']
        contact = request.form['contact_number']
        service_request = ServiceRequest(
            customer_id=curr_login_id,
            service_id=service_id,
            status='requested',
            remarks=remarks,
            contact= contact,
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

@app.route('/customer_dashboard/edit_service_request/<int:curr_login_id>/<int:request_id>', methods=['GET', 'POST'])
def edit_service_request(curr_login_id, request_id):
    customer = User.query.get(curr_login_id)
    if not customer or customer.role != 'customer' or customer.blocked:
        flash('Unauthorized access or You have been blocked by the admin')
        return redirect(url_for('logout'))

    service_request = ServiceRequest.query.get(request_id)
    if not service_request or service_request.customer_id != curr_login_id:
        flash('Service request not found or you do not have permission to edit it.', 'danger')
        return redirect(url_for('customer_dashboard', curr_login_id=curr_login_id))

    if request.method == 'POST':
        # Update remarks for the service request.
        remarks = request.form['remarks']
        service_request.remarks = remarks
        db.session.commit()
        flash('Service request updated successfully!', 'success')
        return redirect(url_for('customer_dashboard', curr_login_id=curr_login_id))

    return render_template('edit_service_request.html', 
                           service_request=service_request, 
                           curr_login_id=curr_login_id)

@app.route('/delete_service_request/<int:curr_login_id>/<int:request_id>', methods=['POST'])
def delete_service_request(curr_login_id, request_id):
    customer = User.query.get(curr_login_id)
    if not customer or customer.role != 'customer' or customer.blocked:
        flash('Unauthorized access or You have been blocked by the admin')
        return redirect(url_for('logout'))

    service_request = ServiceRequest.query.get(request_id)
    if not service_request or service_request.customer_id != curr_login_id:
        flash('Service request not found or you do not have permission to delete it.', 'danger')
        return redirect(url_for('customer_dashboard', curr_login_id=curr_login_id))

    # Deleting service request made by the customer.
    db.session.delete(service_request)
    db.session.commit()
    flash('Service request deleted successfully!', 'success')
    return redirect(url_for('customer_dashboard', curr_login_id=curr_login_id))




@app.route('/customer_dashboard/close_service_request/<int:curr_login_id>/<int:request_id>', methods=['GET', 'POST'])
def close_service_request(curr_login_id, request_id):
    customer = User.query.get(curr_login_id)
    if not customer or customer.role != 'customer' or customer.blocked:
        flash('Unauthorized access or You have been blocked by the admin')
        return redirect(url_for('logout'))

    service_request = ServiceRequest.query.get(request_id)
    if not service_request or service_request.customer_id != curr_login_id or service_request.status != 'completed':
        flash('Service request not found or cannot be closed.')
        return redirect(url_for('customer_dashboard', curr_login_id=curr_login_id))

    if request.method == 'POST':
        # Capture Feedback and ratings( in numeric) given by the customer.
        feedback = request.form.get('feedback')
        rating = int(request.form.get('rating', 0))  

        # Validate the rating
        if rating < 1 or rating > 5:
            flash('Rating must be in between 1 and 5.', 'danger')
            return redirect(url_for('close_service_request', curr_login_id=curr_login_id, request_id=request_id))

        # Updating the service request with feedback, ratings, and status
        service_request.status = 'closed'
        service_request.feedback = feedback
        service_request.rating = rating
        db.session.commit()
        flash('Service request closed successfully with feedback!')
        return redirect(url_for('customer_dashboard', curr_login_id=curr_login_id))

    return render_template('close_service_request.html', service_request=service_request, curr_login_id=curr_login_id)




# -------------------------------- Service Professional Section -------------------------------- #

@app.route('/professional_dashboard/<int:curr_login_id>', methods=['GET'])
def professional_dashboard(curr_login_id):
    professional = User.query.get(curr_login_id)
    if not professional or professional.role != 'professional' or professional.blocked:
        flash('Unauthorized access or You have been blocked by the admin')
        return redirect(url_for('logout'))

    # Fetching all the service requests based on status.
    open_requests = ServiceRequest.query.filter_by(status='requested').all()
    assigned_requests = ServiceRequest.query.filter_by(status='assigned', professional_id=curr_login_id).all()
    closed_requests = ServiceRequest.query.filter_by(status='closed', professional_id=curr_login_id).all()

    return render_template('professional_dashboard.html',
                           professional=professional,
                           open_requests=open_requests,
                           assigned_requests=assigned_requests,
                           closed_requests=closed_requests,
                           curr_login_id=curr_login_id)



@app.route('/accept_service_request/<int:curr_login_id>/<int:request_id>', methods=['POST'])
def accept_service_request(curr_login_id, request_id):
    professional = User.query.get(curr_login_id)
    if not professional or professional.role != 'professional' or professional.blocked:
        flash('Unauthorized access or You have been blocked by the admin')
        return redirect(url_for('logout'))

    service_request = ServiceRequest.query.get(request_id)
    if service_request and service_request.status == 'requested':
        # Assign the service request to the logged-in professional
        service_request.professional_id = curr_login_id
        service_request.status = 'assigned'
        db.session.commit()
        flash('Service request accepted successfully!')
    else:
        flash('Service request not found or already assigned.')

    return redirect(url_for('professional_dashboard', curr_login_id=curr_login_id))

@app.route('/mark_service_completed/<int:curr_login_id>/<int:request_id>', methods=['POST'])
def mark_service_completed(curr_login_id, request_id):
    professional = User.query.get(curr_login_id)
    if not professional or professional.role != 'professional' or professional.blocked:
        flash('Unauthorized access or You have been blocked by the admin')
        return redirect(url_for('logout'))

    service_request = ServiceRequest.query.get(request_id)
    if service_request and service_request.status == 'assigned' and service_request.professional_id == curr_login_id:
        # Updating the status of the service request to 'completed'.
        service_request.status = 'completed'
        service_request.date_of_completion = datetime.now() # fetching date and time of completion.
        db.session.commit()
        flash('Service marked as completed successfully!')
    else:
        flash('Service request not found or cannot be marked as completed.')

    return redirect(url_for('professional_dashboard', curr_login_id=curr_login_id))




@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__=="__main__":
    app.run(port=5500,debug=True)




