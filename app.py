from flask import Flask, render_template, redirect, session, request, flash, url_for
from models import connect_db, db, User, Feedback, get_user_by_username, get_feedback_by_id
from forms import RegisterForm, LoginForm, AddFeedbackForm

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///users'
app.config['SQLALCHECMY_ECHO'] = True
app.config['SECRET_KEY'] = 'prEttYSecRet45'
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

connect_db(app)

with app.app_context():
    db.drop_all()
    db.create_all()

@app.route('/')
def show_home_page():
    """Shows home page."""
    return redirect('/register')


@app.route('/users/<username>')
def show_secret(username):
    """Shows info about the user."""
    user=get_user_by_username(username)
    if not user:
        flash("User not found.")
        return redirect('/')

    feedbacks=user.feedbacks
    if "user_id" not in session:
        flash("Please login first!")
        return redirect('/login')
    return render_template('user_details.html', user=user, feedbacks=feedbacks)


@app.route('/register', methods=['GET', 'POST'])
def register_user():
    """Register form for user."""
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        new_user = User.register(username, password, email, first_name, last_name)

        db.session.add(new_user)
        db.session.commit()
        session['user_id'] = new_user.id
        flash('Welcome! You successfully made your account')
        return redirect(url_for('.show_secret', username=username))
    else:
        return render_template('register.html', form=form)
    

@app.route('/login', methods=['GET', 'POST'])
def login_user():
    """Login form for user."""
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user:
            flash(f"Welcome Back {user.username}!")
            session['user_id'] = user.id
            return redirect(url_for('.show_secret', username=username))
        else:
            form.username.errors = ['Invalid username/password.']

    return render_template('login.html', form=form)


@app.route('/logout')
def logout_user():
    flash(f'Goodbye!')
    session.pop('user_id')
    return redirect('/')


@app.route('/users/<username>/feedback/add', methods=['GET', 'POST'])
def show_add_feedback_form(username):
    """Shows the form for a user to add feedback."""
    if "user_id" not in session:
        flash("Please login first!")
        return redirect('/login')
    form = AddFeedbackForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        new_feedback = Feedback(title=title, content=content, username=username)

        db.session.add(new_feedback)
        db.session.commit()
        return redirect(url_for('.show_secret', username=username))
    else:
        form.content.errors = ['Please fill out all the fields with text.']

    return render_template('feedback_form.html', form=form)


@app.route('/feedback/<feedback_id>/delete', methods=['POST'])
def delete_feedback(feedback_id):
    """Deletes the feedback."""
    if "user_id" not in session:
        flash("Please login first!")
        return redirect('/login')
    
    feedback = Feedback.query.get_or_404(feedback_id)
    user = feedback.user
    username = user.username
    if feedback.username != username:
        flash("You do not have permission to delete this feedback.")
        return redirect(url_for('show_secret', username=username))
    db.session.delete(feedback)
    db.session.commit()
    flash("Successfully deleted the feedback!")
    return redirect(url_for('show_secret', username=username))


@app.route('/users/<username>/delete', methods=['POST'])
def delete_user(username):
    """Deletes the current user from the database."""
    if "user_id" not in session:
        flash("Please login first!")
        return redirect('/login')
    
    current_user_id = session["user_id"]

    user = get_user_by_username(username)
    if not user:
        flash("User not found.")
        return redirect('/')
    
    # Check if the current user is trying to delete themselves
    if user.id != current_user_id:
        flash("You can only delete your own account.")
        return redirect('/users/<username>')
    
    db.session.delete(user)
    db.session.commit()
    flash("Successfully deleted the user.")
    return redirect('/')


@app.route('/feedback/<feedback_id>/edit', methods=['POST', 'GET'])
def show_update_feedback_form(feedback_id):
    """Shows form to update feedback."""
    feedback = get_feedback_by_id(feedback_id)
    if feedback is None:
        flash("Feedback not found.")
        return redirect('/')

    form = AddFeedbackForm(obj=feedback)

    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        
        feedback.title = title
        feedback.content = content
        db.session.commit()
        return redirect(url_for('.show_secret', username=feedback.user.username))
    else: 
        form.content.errors = ['Please make sure you have changed something.']
    return render_template('feedback_update.html', form=form)
    