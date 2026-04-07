from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from lib.python.account.auth import verify_password, create_access_token, get_password_hash, SECRET_KEY, ALGORITHM
from db.database import engine, get_db
import db.models as models
import db.schemas as schemas
import os
import sys
import uuid
from typing import Optional

# --- 1. SETUP PATHS FOR VIDEOPOSE3D ---
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    vp3d_path = os.path.join(project_root, 'VideoPose3dRepo', 'VideoPose3D')
    
    if os.path.exists(vp3d_path):
        sys.path.append(vp3d_path)
    else:
        print(f"WARNING: VideoPose3D path not found at: {vp3d_path}")
except Exception as e:
    print(f"Error setting up paths: {e}")

# Import the Celery task
from worker.tasks import process_swing_video
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# Create Tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Golf Coach API")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Temp Dir Setup
TEMP_DIR = os.path.join(os.getcwd(), "temp_uploads")
os.makedirs(TEMP_DIR, exist_ok=True)

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

# --- AUTH DEPENDENCY ---
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None: raise credentials_exception
    except JWTError: raise credentials_exception
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None: raise credentials_exception
    return user

# --- AUTH ENDPOINTS ---
@app.post("/api/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# --- USER ENDPOINTS ---
@app.post("/api/users", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pwd = get_password_hash(user.password)
    new_user = models.User(email=user.email, username=user.username, hashed_password=hashed_pwd)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/api/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    """Returns the currently logged-in user's details."""
    return current_user

@app.put("/api/users/me/password")
def update_password(
    password_data: schemas.PasswordUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Verifies the current password and updates it with a new hash."""
    # 1. Verify the current password is correct
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    
    # 2. Hash the new password and update the user
    current_user.hashed_password = get_password_hash(password_data.new_password)
    
    # 3. Save to database
    db.commit()
    return {"message": "Password updated successfully"}

# --- SWING ANALYSIS ENDPOINTS ---
@app.post("/api/swings", response_model=schemas.SwingJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def analyze_swing_endpoint(
    video_file_dtl: UploadFile = File(...),
    video_file_fo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user) # NOW PROTECTED
):
    job_id = str(uuid.uuid4())
    
    # Create DB record linked to the logged-in user
    new_job = models.SwingJob(
        id=job_id,
        status="pending",
        user_id=current_user.id # Sarah now owns this swing!
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    # 3. Save Files
    dtl_path = os.path.join(TEMP_DIR, f"{job_id}_dtl.mp4")
    fo_path = os.path.join(TEMP_DIR, f"{job_id}_fo.mp4")

    try:
        with open(dtl_path, "wb") as buffer:
            buffer.write(await video_file_dtl.read())
            
        with open(fo_path, "wb") as buffer:
            buffer.write(await video_file_fo.read())

        # 4. Trigger Celery Task
        # IMPORTANT: We pass the job_id to the task!
        process_swing_video.delay(job_id, dtl_path, fo_path)

        # Update status to processing now that it's in the queue
        new_job.status = "processing"
        db.commit()

    except Exception as e:
        # If saving files or triggering Celery fails, log it in DB
        new_job.status = "failed"
        new_job.error_message = f"Submission failed: {str(e)}"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

    # 5. Return the Job Object
    # The frontend will use the 'id' from this object to poll GET /api/swings/{id}
    return new_job 

@app.get("/api/swings/{job_id}", response_model=schemas.SwingJobResponse)
def get_swing_result(job_id: str, db: Session = Depends(get_db)):
    job = db.query(models.SwingJob).filter(models.SwingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/api/swings", response_model=list[schemas.SwingJobResponse])
def get_user_swings(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """Returns all swing analyses belonging to the logged-in user."""
    return db.query(models.SwingJob).filter(models.SwingJob.user_id == current_user.id).order_by(models.SwingJob.created_at.desc()).all()