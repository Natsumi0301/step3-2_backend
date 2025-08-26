from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, date # dateをインポート
from typing import List, Optional
import math
import models
import schemas

def get_random_recommendation_by_color(db: Session, color_id: int) -> Optional[models.Recommendation]:
    return db.query(models.Recommendation).filter(
        models.Recommendation.color_id == color_id
    ).order_by(func.random()).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user_data: schemas.RegisterRequest, hashed_password: str):
    new_user = models.User(
        name=user_data.name,
        email=user_data.email,
        password=hashed_password,
        prefecture=user_data.prefecture,
        birthday=user_data.birthday,
        gender=user_data.gender
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def get_questions_from_db(db: Session) -> List[models.Question]:
    subquery = db.query(
        models.Question,
        func.row_number().over(
            partition_by=models.Question.category_id,
            order_by=func.random()
        ).label('row_num')
    ).subquery()
    questions = db.query(subquery).filter(subquery.c.row_num == 1).all()
    # SQLAlchemyのRowオブジェクトからQuestionモデルのインスタンスを正しく取り出す
    return [q[0] for q in questions]

def get_random_recommendations_by_color_id(db: Session, color_id: int, limit: int) -> List[models.Recommendation]:
    # rand()からrandom()に統一
    return db.query(models.Recommendation).filter(
        models.Recommendation.color_id == color_id
    ).order_by(func.random()).limit(limit).all()

def get_weekly_records_from_db(db: Session, user_id: int) -> List[models.DailyRecord]:
    today = datetime.now().date()
    one_week_ago = today - timedelta(days=7)
    return db.query(models.DailyRecord).filter(
        models.DailyRecord.user_id == user_id,
        models.DailyRecord.check_in_date >= one_week_ago
    ).order_by(models.DailyRecord.check_in_date).all()

# ▼▼▼【ここから全面的に修正】▼▼▼
def save_daily_record_to_db(db: Session, user_id: int, answers: List[schemas.AnswerData], color_id: int, check_in_date: date):
    """
    日々の記録と回答をDBに保存する。
    指定されたユーザーと日付の記録が既に存在すれば更新し、なければ新規作成する (Upsert)。
    """
    
    # 1. 指定されたユーザーIDと日付で既存の記録を検索
    existing_record = db.query(models.DailyRecord).filter(
        models.DailyRecord.user_id == user_id,
        models.DailyRecord.check_in_date == check_in_date
    ).first()

    recommendation = get_random_recommendation_by_color(db, color_id=color_id)
    recommend_id = recommendation.recommend_id if recommendation else None

    if existing_record:
        # 2. 記録が存在する場合：内容を更新
        existing_record.color_id = color_id
        existing_record.recommend_id = recommend_id
        
        # 紐づく既存の回答を一度すべて削除
        db.query(models.DailyAnswer).filter(models.DailyAnswer.check_id == existing_record.check_id).delete()
        
        # この後の回答保存処理で使うため、更新対象のレコードを代入
        record_to_process = existing_record
        
    else:
        # 3. 記録が存在しない場合：新規に作成
        new_record = models.DailyRecord(
            user_id=user_id,
            check_in_date=check_in_date, # 引数の日付を使用
            color_id=color_id,
            recommend_id=recommend_id
        )
        db.add(new_record)
        db.flush() # new_record.check_id をDBセッション内で確定させる
        record_to_process = new_record

    # 4. 新しい回答を保存
    for answer_data in answers:
        new_answer = models.DailyAnswer(
            check_id=record_to_process.check_id,
            question_id=answer_data.question_id,
            answer_choice=answer_data.answer_choice
        )
        db.add(new_answer)
    
    # 全ての変更をまとめてコミット
    db.commit()
# ▲▲▲【ここまで全面的に修正】▲▲▲


def create_lantan_for_user(db: Session, user_id: int) -> Optional[models.Lantan]:
    weekly_records = get_weekly_records_from_db(db, user_id=user_id)
    if not weekly_records:
        return None

    color_ids = [record.color_id for record in weekly_records if record.color_id is not None]
    if not color_ids:
        return None

    average_color = sum(color_ids) / len(color_ids)
    lantan_color_value = int(round(average_color))

    new_lantan = models.Lantan(
        user_id=user_id,
        lantan_color=lantan_color_value
    )
    db.add(new_lantan)
    db.commit()
    db.refresh(new_lantan)
    
    return new_lantan
