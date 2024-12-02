from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated, List, Optional
from sqlmodel import Field, Session, SQLModel, create_engine, select, Relationship
from contextlib import asynccontextmanager
import pandas as pd

# Models
class Announcement(SQLModel, table = True):
    id: int = Field(default=None, primary_key=True)    
    user_name: str
    tag: str
    description: str

# Association tables for mentors and teammates
class MentorLink(SQLModel, table=True):
    mentor_id: int = Field(foreign_key="user.id", primary_key=True)
    mentee_id: int = Field(foreign_key="user.id", primary_key=True)

class TeammateLink(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    teammate_id: int = Field(foreign_key="user.id", primary_key=True)

# Main User model
class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    password: str
    role: str  # Roles: [STUDENT, MENTOR, TEACHER]
    imgURL: str
    linkdinURL: str
    githubURL: str
    websiteURL: Optional[str] = None
    resumeURL: Optional[str] = None

    # Teacher-Student Relationship (Many-to-One)
    teacher_id: Optional[int] = Field(default=None, foreign_key="user.id")
    teacher: Optional["User"] = Relationship(
        back_populates="students", 
        sa_relationship_kwargs={"remote_side": "User.id"}
    )
    students: List["User"] = Relationship(
        back_populates="teacher"
    )

    # Mentors (Many-to-Many)
    mentors: List["User"] = Relationship(
        back_populates="mentees",
        link_model=MentorLink,
        sa_relationship_kwargs={
            "primaryjoin": "User.id==MentorLink.mentee_id",
            "secondaryjoin": "User.id==MentorLink.mentor_id"
        }
    )
    mentees: List["User"] = Relationship(
        back_populates="mentors",
        link_model=MentorLink,
        sa_relationship_kwargs={
            "primaryjoin": "User.id==MentorLink.mentor_id",
            "secondaryjoin": "User.id==MentorLink.mentee_id"
        }
    )



    # Teammates (Self-Referential Many-to-Many)
    teammates: List["User"] = Relationship(
        link_model=TeammateLink,
        sa_relationship_kwargs={
            "primaryjoin": "User.id==TeammateLink.user_id",
            "secondaryjoin": "User.id==TeammateLink.teammate_id"
        }
    )

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

    # Aryan Info
    aryan_img_url = "https://media.licdn.com/dms/image/v2/D4E35AQH0AwVtQ2-fug/profile-framedphoto-shrink_400_400/profile-framedphoto-shrink_400_400/0/1721141409771?e=1733724000&v=beta&t=jmpNYpfjBzGmvT3Ys0Uh5GBXDizN4Ffgk06a8d97lAE"
    aryan_linkdin_url = "https://www.linkedin.com/in/aryanjain06/"
    aryan_github_url = "https://github.com/aryanj112"

    # Aditi Info
    aditi_img_url = "https://media.licdn.com/dms/image/v2/D4E03AQEMlHUEHVLA2A/profile-displayphoto-shrink_400_400/profile-displayphoto-shrink_400_400/0/1726514279485?e=1738800000&v=beta&t=uor6AokOWHCl5eOJTFTgg2f6TtXq0hCzFYWbjsCupXM"
    aditi_linkdin_url = "https://www.linkedin.com/in/-aditisethi/"
    aditi_github_url = "https://github.com/aditisethi15"

    # Gavin Info
    gavin_img_url = "https://media.licdn.com/dms/image/v2/D5603AQGurWafPZmY3A/profile-displayphoto-shrink_400_400/profile-displayphoto-shrink_400_400/0/1712186812396?e=1738800000&v=beta&t=8ZDT-Nu_xUZQLHM_1k5jbTFciY1pjr0Ms3vdqiO5cqw"
    gavin_github_url = "https://github.com/gavinkhung"
    gavin_linkdin_url = "https://www.linkedin.com/in/gavinkhung/"
    gavin_website_url = "https://www.gavinkhung.me/"
    gavin_resume_url = "https://www.gavinkhung.me/resume.pdf"

    # Kimber Info
    kimber_img_url = "https://webv2-backend.appdevclub.com/team-images/kimber-gonzalez-lopez.jpeg"
    kimber_linkdin_url = "https://www.linkedin.com/in/kimber-gonzalez-lopez/"
    kimber_github_url = "https://github.com/KiberVG"

    aryan = User(name="Aryan", password="pass123", role="STUDENT", imgURL=aryan_img_url, linkdinURL=aryan_linkdin_url, githubURL=aryan_github_url)
    aditi = User(name="Aditi", password="pass123", role="STUDENT", imgURL=aditi_img_url, linkdinURL=aditi_linkdin_url, githubURL=aditi_github_url)
    gavin = User(name="Gavin", password="mentor123", role="MENTOR", imgURL=gavin_img_url, linkdinURL=gavin_linkdin_url, githubURL=gavin_github_url, websiteURL = gavin_website_url, resumeURL = gavin_resume_url)
    kimber = User(name="Kimber", password="teach123", role="TEACHER", imgURL=kimber_img_url, linkdinURL=kimber_linkdin_url, githubURL=kimber_github_url)

    aryan.teammates.append(aditi)
    aditi.teammates.append(aryan)

    kimber.teammates.append(gavin)
    gavin.teammates.append(kimber)

    aryan.teacher = kimber
    aditi.teacher = kimber

    gavin.mentees.append(aryan)
    gavin.mentees.append(aditi)

    kimber.students.append(aryan)
    kimber.students.append(aditi)

    with Session(engine) as session:
        session.add_all([aryan,aditi,kimber,gavin])
        session.commit()

    # Populate Announcements from CSV
    df_announcements = pd.read_csv("data/announcements.csv")
    announcements = []
    for _, row in df_announcements.iterrows():
        announcement = Announcement(
            # id=int(row['id']),
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