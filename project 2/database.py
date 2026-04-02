from sqlalchemy import create_engine, Column, Integer, String, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Security context for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False) # 'student' or 'professor'

# Initialize and seed database
def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Check if users already exist
        if db.query(User).count() == 0:
            print("Seeding database with default users...")
            # Default Student
            student = User(
                email="student@health.ai",
                password_hash=pwd_context.hash("student123"),
                role="student"
            )
            # Default Professor
            professor = User(
                email="professor@health.ai",
                password_hash=pwd_context.hash("professor123"),
                role="professor"
            )
            db.add(student)
            db.add(professor)
            db.commit()
            print("Database seeded successfully.")
    finally:
        db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
