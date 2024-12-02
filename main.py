from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated
from sqlmodel import Field, Session, SQLModel, create_engine, select
from contextlib import asynccontextmanager


class Announcement(SQLModel, table = True):
    id: int = Field(default=None, primary_key=True)    
    author: str
    tag: str
    description: str
    imgUrl: str

sqlite_database_name = "bootcampPortalDatabase.db"
sqlite_url = f"sqlite:///{sqlite_database_name}"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args, echo=True)
 
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        default_announcements = [
            Announcement(
                author = "Kimber", 
                tag = "@Homework", 
                description = "There is no homework due to the hackathon", 
                imgUrl = "https://webv2-backend.appdevclub.com/team-images/kimber-gonzalez-lopez.jpeg"
            ),
            Announcement(
                author = "Aidan", 
                tag = "@Events", 
                description = "There is a new event happening on Tuesday from 6:30-7:30", 
                imgUrl = "https://webv2-backend.appdevclub.com/team-images/aidan-melvin.jpeg"
            ),
            Announcement(
                author = "Kimber", 
                tag = "@Help", 
                description = "I need some members to help me make a website, dm if interested", 
                imgUrl = "https://webv2-backend.appdevclub.com/team-images/kimber-gonzalez-lopez.jpeg"
            ),
        ]

        existing = session.exec(select(Announcement)).all()

        if not existing:
            session.add_all(default_announcements)
            session.commit()

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