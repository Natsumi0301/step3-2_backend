import hashlib
from typing import List
from fastapi import FastAPI, Depends, HTTPException, APIRouter, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import crud, models, schemas, auth
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])
main_api_router = APIRouter(tags=["Main API"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def generate_color_id_from_answers(answers: List[schemas.AnswerData]) -> int:
    if not answers: return 3
    avg_score = sum(ans.answer_choice for ans in answers) / len(answers)
    if avg_score >= 4.5: return 5
    if avg_score >= 3.5: return 4
    if avg_score >= 2.5: return 3
    if avg_score >= 1.5: return 2
    return 1

# --- メインAPI ---

@main_api_router.post("/mood/save")
async def save_mood(
    mood_data: schemas.MoodDataForSave,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    color_id = generate_color_id_from_answers(mood_data.answers)
    crud.save_daily_record_to_db(
        db, user_id=current_user.user_id, answers=mood_data.answers, color_id=color_id
    )
    return {"message": "Mood data saved successfully", "color_id": color_id}

@main_api_router.get("/mood/week")
async def get_weekly_colors(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    weekly_data = crud.get_weekly_records_from_db(db, user_id=current_user.user_id)
    return {"color_ids": [record.color_id for record in weekly_data]}

@main_api_router.get("/questions", response_model=schemas.QuestionsResponse)
def get_questions(db: Session = Depends(get_db)):
    questions_from_db = crud.get_questions_from_db(db)
    return schemas.QuestionsResponse(questions=questions_from_db)


#レコメンデーション
@main_api_router.post("/recommendations", response_model=List[schemas.RecommendationResponse])
def get_recommendations(
    request: schemas.RecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    スコア（color_id）に基づいてレコメンドをランダムに2つ取得する
    """
    # 新しく作成した、件数指定でランダム取得する関数を呼び出す
    recommendations = crud.get_random_recommendations_by_color_id(
        db, color_id=request.score, limit=2
    )

    if not recommendations:
        # 該当するレコメンドがない場合は空のリストを返す
        return []
        
    return recommendations


# 【新規作成】ランタンをリリースするAPI
@main_api_router.post("/lantan/release", response_model=schemas.LantanReleaseResponse)
def release_lantan(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """【ログイン必須】直近1週間の色の平均からランタンを作成し、リリースする"""
    new_lantan = crud.create_lantan_for_user(db, user_id=current_user.user_id)
    
    if not new_lantan:
        raise HTTPException(
            status_code=404,
            detail="過去1週間の記録が見つからないため、ランタンを作成できませんでした。"
        )
        
    return {
        "message": "Lantan released successfully!",
        "lantan": new_lantan
    }

# --- 認証API ---

@auth_router.post("/register", response_model=schemas.LoginResponse)
def register(register_data: schemas.RegisterRequest, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, email=register_data.email):
        raise HTTPException(status_code=400, detail="このメールアドレスは既に使用されています")
    
    hashed_password = hashlib.sha256(register_data.password.encode()).hexdigest()
    new_user = crud.create_user(db, user_data=register_data, hashed_password=hashed_password)
    
    access_token = auth.create_access_token(data={"sub": new_user.email})
    
    # login と同じ形式で、トークンとユーザー情報を返す
    return {
        "token": access_token,
        "token_type": "bearer",
        "user": {
            "id": new_user.user_id,
            "username": new_user.name,
            "email": new_user.email,
            "name": new_user.name
        }
    }

@auth_router.post("/login") # response_modelを後述のLoginResponseに変更
def login(
    login_data: schemas.LoginRequest, # Form(...) から LoginRequestモデルに変更
    db: Session = Depends(get_db)
):
    # login_data.email でデータにアクセス
    user = crud.get_user_by_email(db, email=login_data.email) 
    if not user or user.password != hashlib.sha256(login_data.password.encode()).hexdigest():
        raise HTTPException(
            status_code=401, 
            detail="メールアドレスまたはパスワードが間違っています"
        )

    access_token = auth.create_access_token(data={"sub": user.email})
    
    # フロントエンドが期待するユーザー情報も一緒に返す
    return {
        "token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.user_id,
            "username": user.name, # jsxの'username'キーに合わせる
            "email": user.email,
            "name": user.name
        }
    }

app.include_router(main_api_router)
app.include_router(auth_router)
