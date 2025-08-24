from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Optional
import math
import models
import schemas

def get_random_recommendation_by_color(db: Session, color_id: int) -> Optional[models.Recommendation]:
    """
    指定されたcolor_idに紐づくレコメンドの中から、ランダムに1つを取得する。
    """
    return db.query(models.Recommendation).filter(
        models.Recommendation.color_id == color_id
    ).order_by(func.rand()).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """メールアドレスでユーザーを検索する"""
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user_data: schemas.RegisterRequest, hashed_password: str):
    """新規ユーザーを作成する"""
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
    """DBから各カテゴリの質問をランダムに1問ずつ取得する"""
    subquery = db.query(
        models.Question,
        func.row_number().over(
            partition_by=models.Question.category_id,
            order_by=func.rand()
        ).label('row_num')
    ).subquery()
    questions = db.query(subquery).filter(subquery.c.row_num == 1).all()
    return questions

def get_random_recommendations_by_color_id(db: Session, color_id: int, limit: int) -> List[models.Recommendation]:
    """
    指定されたcolor_idに紐づくレコメンドを、指定された件数だけランダムに取得する。
    """
    return db.query(models.Recommendation).filter(
        models.Recommendation.color_id == color_id
    ).order_by(func.rand()).limit(limit).all()

def get_weekly_records_from_db(db: Session, user_id: int) -> List[models.DailyRecord]:
    """DBから直近7日間の記録を取得する"""
    today = datetime.now().date()
    one_week_ago = today - timedelta(days=7)
    return db.query(models.DailyRecord).filter(
        models.DailyRecord.user_id == user_id,
        models.DailyRecord.check_in_date >= one_week_ago
    ).order_by(models.DailyRecord.check_in_date).all()

def save_daily_record_to_db(db: Session, user_id: int, answers: List[schemas.AnswerData], color_id: int):
    """日々の記録と回答をDBに保存する"""
    today = datetime.now().date()
    
    recommendation = get_random_recommendation_by_color(db, color_id=color_id)
    recommend_id = recommendation.recommend_id if recommendation else None

    new_record = models.DailyRecord(
        user_id=user_id,
        check_in_date=today,
        color_id=color_id,
        recommend_id=recommend_id
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    for answer_data in answers:
        new_answer = models.DailyAnswer(
            check_id=new_record.check_id,
            question_id=answer_data.question_id,
            answer_choice=answer_data.answer_choice
        )
        db.add(new_answer)
    db.commit()

def create_lantan_for_user(db: Session, user_id: int) -> Optional[models.Lantan]:
    """直近1週間の色の平均を算出し、新しいランタンを作成する"""
    weekly_records = get_weekly_records_from_db(db, user_id=user_id)
    if not weekly_records:
        return None

    color_ids = [record.color_id for record in weekly_records if record.color_id is not None]
    if not color_ids:
        return None

    average_color = sum(color_ids) / len(color_ids)
    lantan_color_value = int(round(average_color))

    # Lantanモデルのlantan_color列に値を保存する
    new_lantan = models.Lantan(
        user_id=user_id,
        lantan_color=lantan_color_value
    )
    db.add(new_lantan)
    db.commit()
    db.refresh(new_lantan)
    
    return new_lantan
