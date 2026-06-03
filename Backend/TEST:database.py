from sqlalchemy import String, create_engine, Column, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import IntegrityError

# Set-up Database
engine = create_engine("sqlite:///test.db", echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

# Define Models (User / Tasks)
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)

    tasks = relationship('Task', back_populates='user', cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    title = Column(String(50), nullable=True)
    description = Column(String)

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', back_populates='tasks')

Base.metadata.create_all(engine)

# Utility Functions
def get_user_by_email(email):
    return session.query(User).filter(email=email).first()

def confirm_action(prompt:str) -> bool:
    return input(f"{prompt} (yes/no): ".strip().lower()) == 'yes'


# CRUD
def add_user():
    name, email = input("Enter username"), input("Enter the email")
    if get_user_by_email(email):
        print(f"User already exists {email}")
    
    try:
        session.add(User(name=name, email=email))
        session.commit()
        print(f"User: {name} added")
    
    except IntegrityError:
        session.rollback()
        print("Error")


def add_task():
    email = input("Enter the email of the user to add tasks: ")
    user = get_user_by_email(email)
    if not user:
        print("No user found with that email")
    
    title, description = input("Enter the title: "), input("Enter the description: ")
    session.add(Task(title=title, description=description, user=user))
    session.commit()
    print(f"Added to the database: {title}, {description}")



def user_query():
    for user in session.query(User).all():
        print(f"ID: {user.id}, Name {user.name}, Email {user.email}")



def query_task():
    email = input("Enter the email for the user for tasks: ")
    user = session.query(User).filter_by(email=email).first()
    if not user:
        print("No user found in the database")
    
    for task in user.tasks:
        print(f"Task ID: {task.id}, Title: {task.title}")

def update_user():
    email = input("Email of who you want to update")
    user = get_user_by_email(email)

    if not user:
        print("No user with that email")
    
    user.name = input("Enter a new name for the user: ")
    user.email = input("Enter a new email for the user")
    session.commit()
    print("User updated")

def delete_user():
    email = input("Email of who you want to update")
    user = get_user_by_email(email)

    if not user:
        print("No user with that email")
    
    if confirm_action(f"Are you sure you want to delete: {user.name}?"):
        session.delete(user)
        session.commit()
        print("User has been deleted")

def delete_task():
    task_id = input("Enter the ID of the task you want to delete")
    task = session.query(Task).get(task_id)
    if not task:
        print("There is no task there")
    
    if confirm_action(f"Are you sure you wan to delete this task: {task_id}?"):
        session.delete(task)
        session.commit()
        print("Task deleted")

def update_task():
    task_id = input("Enter the ID of the task you want to update")
    task = session.query(Task).get(task_id)

    if not task:
        print("There is no task there")
    
    task.title = input("Enter new task: ")
    task.description = input("Enter a description for the new task")
    
    session.commit()
    print("Task updated")


# Action
def main() -> None:
    actions = {
        "1":add_user,
        "2":add_task,
        "3":user_query,
        "4":query_task,
        "5":update_user,
        "6":delete_user,
        "7":delete_task,
        "8":update_task
    }

    while True:
        print("\nOptions: \n1. Add User\n2. Add Task\n3. Query Users\n4. Query Tasks\n5. Update User\n6. DeleteUser\n7. Delete Task\n8. Update Task\n9. Exit")

        choice = input("Enter an option: ")
        if choice == "9":
            print("Bye")
            break

        action = actions.get(choice)
        if action:
            action()
        else:
            print("That is not an option")


if __name__ == "__main__":
    main()