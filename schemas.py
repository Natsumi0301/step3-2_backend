from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import List, Optional

# --- 基本モデル ---
class QuestionCategory(BaseModel):
    category_id: int
    category_name: str
    model_config = ConfigDict(from_attributes=True)

class Color(BaseModel):
    color_id: int
    color_name: str | None = None
    model_config = ConfigDict(from_attributes=True)

class Question(BaseModel):
    question_id: int
    question_text: str
    category: QuestionCategory
    model_config = ConfigDict(from_attributes=True)

class User(BaseModel):
    user_id: int
    email: str
    name: str
    model_config = ConfigDict(from_attributes=True)

# --- リクエストボディ ---
class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    prefecture: Optional[str] = None
    birthday: Optional[date] = None
    gender: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class AnswerData(BaseModel):
    question_id: int
    answer_choice: int

class MoodDataForSave(BaseModel):
    answers: List[AnswerData]

# --- レスポンスボディ ---
class Token(BaseModel):
    access_token: str
    token_type: str

class QuestionsResponse(BaseModel):
    questions: List[Question]

# 【新規作成】Lantanモデル
class Lantan(BaseModel):
    lantan_id: int
    released_at: datetime
    user_id: int
    color_id: int
    model_config = ConfigDict(from_attributes=True)

# 【新規作成】Lantanリリース時のレスポンスモデル
class LantanReleaseResponse(BaseModel):
    message: str
    lantan: Lantan
