from flask import Flask, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, Date
from datetime import datetime, date
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
Bootstrap5(app)

login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///TsuiTodo.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)



class User(UserMixin, db.Model):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    todos = relationship("Todo", back_populates="user")



class Todo(db.Model):
    __tablename__ = "todo"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Insert Title
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    # Connect User
    user = relationship("User", back_populates="todos")
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("user.id"))
    tasks = relationship("Task", back_populates="title", cascade="all, delete")

class Task(db.Model):
    __tablename__ = "task"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Insert Task
    info: Mapped[str] = mapped_column(String(500), nullable=False)
    due: Mapped[date] = mapped_column(Date, nullable=True)
    # Connect Title
    title = relationship("Todo", back_populates="tasks")
    title_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("todo.id"))
    # Toggle Star
    important: Mapped[bool] = mapped_column(Boolean, default=False)


with app.app_context():
    db.create_all()


@app.route("/", methods=['GET','POST'])
def home():
    # Check if a User is Signed In
    if current_user.is_authenticated:
        # Create New Task List
        if request.method == 'POST':
            data = request.form
            new_todo = Todo(
                title= data['todoTitle'],
                user = current_user
            )
            first_task = Task(
                info = data['firstTask'],
                title = new_todo
            )
            date_str = data['date']
            if date_str:
                due = datetime.strptime(date_str, '%Y-%m-%d').date()
                first_task.due = due
            db.session.add(new_todo)
            db.session.add(first_task)
            db.session.commit()
            return redirect(url_for("show_todo", todo_id=new_todo.id))

        # New Task List Form Page
        return render_template("create.html", current_user=current_user)

    # Register New User
    if request.method == 'POST':
        data = request.form
        result = db.session.execute(db.select(User).where(User.email == data['email']))
        user = result.scalar()
        if user:
            flash("You've already signed up with that email, log in instead.")
            return redirect(url_for('login'))
        new_user = User(
            email = data['email'],
            password = data['password']
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return render_template("create.html", current_user=current_user)

    # Sign Up Page
    return render_template("index.html")

@app.route("/login", methods=['GET','POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        result = db.session.execute(db.select(User).where(User.email == request.form['email']))
        user = result.scalar()

        # Incorrect Email
        if not user:
            flash("That email does not exist, please try again or Sign Up below.")
            return redirect(url_for('login'))

        # Incorrect Password
        elif user.password != password:
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))

        # Correct Login
        else:
            login_user(user)
            return redirect(url_for('home'))

    return render_template("login.html")

@app.route("/log_out")
@login_required
def log_out():
    logout_user()
    return redirect(url_for('home'))

@app.route("/todo/<int:todo_id>")
@login_required
def show_todo(todo_id):
    requested_todo = db.get_or_404(Todo, todo_id)
    try:
        result = db.session.execute(db.select(Task).where(Task.title_id == todo_id, Task.important == False))
        tasks = result.scalars().all()
    except NoResultFound:
        tasks = []
    try:
        impres = db.session.execute(db.select(Task).where(Task.title_id == todo_id, Task.important == True))
        imp = impres.scalars().all()
    except NoResultFound:
        imp = []

    return render_template("todo.html", todo=requested_todo, current_user=current_user, tasks=tasks, important=imp)

@app.route("/change_title/<int:todo_id>", methods=['POST'])
@login_required
def change_title(todo_id):
    todo = db.get_or_404(Todo, todo_id)
    todo.title = request.form["title"]
    db.session.add(todo)
    db.session.commit()
    return redirect(url_for("show_todo", todo_id=todo_id))

@app.route("/change_task", methods=['POST'])
@login_required
def change_task():
    data = request.form
    current_task = db.get_or_404(Task, data["taskId"])
    current_task.info = data["task"]
    date_str = data['date']
    if date_str:
        due = datetime.strptime(date_str, '%Y-%m-%d').date()
        current_task.due = due
    db.session.add(current_task)
    db.session.commit()
    return redirect(url_for("show_todo", todo_id=current_task.title_id))

@app.route("/add_task/<int:todo_id>", methods=['POST'])
@login_required
def add_task(todo_id):
    current_todo = db.get_or_404(Todo, todo_id)
    new_task = Task(
        info = request.form['task'],
        title = current_todo,
        due = None
    )
    date_str = request.form['date']
    if date_str:
        due = datetime.strptime(date_str, '%Y-%m-%d').date()
        new_task.due = due
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for("show_todo", todo_id=todo_id))


@app.route("/star/<int:task_id>")
@login_required
def star(task_id):
    task = db.get_or_404(Task, task_id)
    if task.important:
        task.important = False
    else:
        task.important = True
    db.session.add(task)
    db.session.commit()
    return redirect(url_for("show_todo", todo_id=task.title.id))

@app.route("/delete_todo/<int:todo_id>")
@login_required
def delete_todo(todo_id):
    todo_delete = db.get_or_404(Todo, todo_id)
    db.session.delete(todo_delete)
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/delete_task/<int:task_id>")
@login_required
def delete_task(task_id):
    task_delete = db.get_or_404(Task, task_id)
    db.session.delete(task_delete)
    db.session.commit()
    return redirect(url_for("show_todo", todo_id=task_delete.title_id))

if __name__ == "__main__":
    app.run(debug=True)