from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated, List, Optional
from sqlmodel import Field, Session, SQLModel, create_engine, select
from contextlib import asynccontextmanager
import pandas as pd

# Models
class Announcement(SQLModel, table = True):
    id: int = Field(default=None, primary_key=True)    
    user_name: str
    tag: str
    description: str

class User(SQLModel, table = True):
    id: int = Field(default=None, primary_key=True)    
    name: str # User John Doe will have the name: "John Doe"
    password: str
    role: str # Roles include: [STUDENT, MENTOR, TEACHER]
    
    imgURL: str 
    linkdinURL: str
    githubURL: str
    websiteURL: Optional[str] = None
    resumeURL: Optional[str] = None

    teammates: Optional[List[str]] = None  # List of teammates (names or ids, depending on your logic)
    mentors: Optional[List[str]] = None     # List of mentors (names or ids, depending on your logic)
    students: Optional[List[str]] = None    # List of students (names or ids, depending on your logic)
    teacher: Optional[str] = None      # Optional teacher name, if applicable

# Database setup
sqlite_database_name = "bootcampPortalDatabase.db"
sqlite_url = f"sqlite:///{sqlite_database_name}"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def reset_db_and_tables():
    SQLModel.metadata.drop_all(engine)
    create_db_and_tables()

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Setting up the database...")
    create_db_and_tables()

    # Populate Users from CSV
    df_users = pd.read_csv("users.csv")
    users = []
    for _, row in df_users.iterrows():
        user = User(
            id=int(row['id']),
            name=row['name'],
            password=row['password'],
            role=row['role'],
            imgURL=row['imgURL'],
            linkdinURL=row['linkdinURL'],
            githubURL=row['githubURL'],
            websiteURL=row['websiteURL'] if pd.notna(row['websiteURL']) else None,
            resumeURL=row['resumeURL'] if pd.notna(row['resumeURL']) else None,
            teammates=row['teammates'].split(',') if pd.notna(row['teammates']) else None,
            mentors=row['mentors'].split(',') if pd.notna(row['mentors']) else None,
            students=row['students'].split(',') if pd.notna(row['students']) else None,
            teacher=row['teacher'] if pd.notna(row['teacher']) else None
        )
        users.append(user)

    with Session(engine) as session:
        session.add_all(users)
        session.commit()

    # Populate Announcements from CSV
    df_announcements = pd.read_csv("announcements.csv")
    announcements = []
    for _, row in df_announcements.iterrows():
        announcement = Announcement(
            id=int(row['id']),
            user_name=row['user_name'],
            tag=row['tag'],
            description=row['description']
        )
        announcements.append(announcement)

    with Session(engine) as session:
        session.add_all(announcements)
        session.commit()

    yield
    print("App shutdown")

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/announcements')
async def get_announcements(session: SessionDep):
    announcements = session.exec(select(Announcement)).all()
    return announcements

@app.post('/announcements/new')
async def post_announcement(announcement: Announcement, session: SessionDep):
    session.add(announcement)

    try:
        session.commit()
    except Exception as e:
        session.rollback() 
        raise HTTPException(status_code=500, detail="Database commit failed")  
      
    session.refresh(announcement)
    return announcement 


@app.post('/reset-db')
async def reset_database():
    reset_db_and_tables()
    return {"message": "Database has been reset"}