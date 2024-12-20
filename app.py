from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'Securekey7896'

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# User model to store account information
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# WorkoutLog model to track workouts for users
class WorkoutLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exercise = db.Column(db.String(50), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    calories = db.Column(db.Integer, nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)

# Quote model to store motivational quotes
class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(100), nullable=False)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Both fields are required.', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('This username is already taken.', 'error')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/', methods=['GET', 'POST'])
def index():
    """Handle user login."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Both fields are required.', 'error')
            return redirect(url_for('index'))

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user'] = user.username
            session['user_id'] = user.id
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('home'))

        flash('Invalid username or password.', 'error')

    return render_template('index.html')

@app.route('/home')
def home():
    """Display user statistics and a motivational quote."""
    if 'user' not in session:
        flash('You need to log in first.', 'error')
        return redirect(url_for('index'))

    quote = Quote.query.order_by(db.func.random()).first()
    user_id = session['user_id']

    # Calculate workout stats
    total_calories = db.session.query(db.func.sum(WorkoutLog.calories)).filter_by(user_id=user_id).scalar() or 0
    total_time = db.session.query(db.func.sum(WorkoutLog.duration)).filter_by(user_id=user_id).scalar() or 0
    total_workouts = WorkoutLog.query.filter_by(user_id=user_id).count()

    hours, minutes = divmod(total_time, 60)

    return render_template(
        'home.html',
        username=session['user'],
        quote=quote,
        total_calories=total_calories,
        total_time=f'{hours}h {minutes}m',
        total_workouts=total_workouts
    )

@app.route('/log', methods=['GET', 'POST'])
def log_workout():
    """Log workout details."""
    if 'user' not in session:
        flash('Please log in to log your workout.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        exercise = request.form.get('exercise')
        duration = request.form.get('duration')
        calories = request.form.get('calories')

        if not exercise or not duration:
            flash('Exercise type and duration are required.', 'error')
            return redirect(url_for('log_workout'))

        new_workout = WorkoutLog(
            user_id=session['user_id'],
            exercise=exercise,
            duration=int(duration),
            calories=int(calories) if calories else None
        )
        db.session.add(new_workout)
        db.session.commit()

        flash('Workout logged successfully!', 'success')
        return redirect(url_for('home'))

    return render_template('log_workout.html')

@app.route('/workout_history')
def workout_history():
    """Show logged workouts."""
    if 'user' not in session:
        flash('Please log in to view your workout history.', 'error')
        return redirect(url_for('index'))

    workouts = WorkoutLog.query.filter_by(user_id=session['user_id']).all()
    return render_template('workout_history.html', workouts=workouts)

@app.route('/timer')
def timer():
    """Show workout timer."""
    if 'user' not in session:
        flash('Please log in to access the timer.', 'error')
        return redirect(url_for('index'))

    return render_template('timer.html')

@app.route('/logout')
def logout():
    """Log out the user."""
    session.pop('user', None)
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

def seed_data():
    """Add sample motivational quotes to the database."""
    if not Quote.query.first():
        quotes = [
            Quote(content="What hurts today makes you stronger tomorrow.", author="Jay Cutler"),
            Quote(content="Strength comes from struggle.", author="Arnold Schwarzenegger"),
            Quote(content="Failure is where growth begins.", author="Ronnie Coleman"),
        ]
        db.session.add_all(quotes)
        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_data()
    app.run(debug=True)

