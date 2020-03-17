import uvicorn
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError
from sqlalchemy.orm import Session
from fastapi import Depends, FastAPI, HTTPException
from starlette import status

import crud
import models
import schemas
from app_utils import decode_access_token
from crud import get_user_by_username
from database import engine, SessionLocal
from schemas import UserInfo, TokenData, UserCreate, Token

models.Base.metadata.create_all(bind=engine)

ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()


# Dependency


def get_db():
    db = None
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/authenticate")


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(data=token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except PyJWTError:
        raise credentials_exception
    user = get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


@app.post("/user", response_model=UserInfo)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)


@app.post("/authenticate", response_model=Token)
def authenticate_user(user: schemas.UserAuthenticate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user is None:
        raise HTTPException(status_code=400, detail="Username not existed")
    else:
        is_password_correct = crud.check_username_password(db, user)
        if is_password_correct is False:
            raise HTTPException(status_code=400, detail="Password is not correct")
        else:
            from datetime import timedelta
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            from app_utils import create_access_token
            access_token = create_access_token(
                data={"sub": user.username}, expires_delta=access_token_expires)
            return {"access_token": access_token, "token_type": "Bearer"}


@app.post("/blog", response_model=schemas.Blog)
async def create_new_blog(blog: schemas.BlogBase, current_user: UserInfo = Depends(get_current_user)
                          , db: Session = Depends(get_db)):
    return crud.create_new_blog(db=db, blog=blog)


@app.get("/blog")
async def get_all_blogs(current_user: UserInfo = Depends(get_current_user)
                        , db: Session = Depends(get_db)):
    return crud.get_all_blogs(db=db)


@app.get("/blog/{blog_id}")
async def get_blog_by_id(blog_id, current_user: UserInfo = Depends(get_current_user)
                         , db: Session = Depends(get_db)):
    return crud.get_blog_by_id(db=db, blog_id=blog_id)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8081)
