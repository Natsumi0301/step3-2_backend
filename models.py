from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "user"
    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    prefecture = Column(String(255))
    birthday = Column(Date)
    gender = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    records = relationship("DailyRecord", back_populates="user")
    lantans = relationship("Lantan", back_populates="user")

class DailyRecord(Base):
    __tablename__ = "daily_record"
    check_id = Column(Integer, primary_key=True, index=True)
    check_in_date = Column(Date, nullable=False)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False)
    color_id = Column(Integer, ForeignKey("color.color_id"))
    recommend_id = Column(Integer, ForeignKey("recommendation.recommend_id"))

    user = relationship("User", back_populates="records")
    color = relationship("Color")
    recommendation = relationship("Recommendation")
    answers = relationship("DailyAnswer", back_populates="record", cascade="all, delete-orphan")

class DailyAnswer(Base):
    __tablename__ = "daily_answer"
    answer_id = Column(Integer, primary_key=True, index=True)
    answer_choice = Column(Integer, nullable=False)
    check_id = Column(Integer, ForeignKey("daily_record.check_id"), nullable=False)
    question_id = Column(Integer, ForeignKey("question.question_id"), nullable=False)

    record = relationship("DailyRecord", back_populates="answers")
    question = relationship("Question")

class Question(Base):
    __tablename__ = "question"
    question_id = Column(Integer, primary_key=True, index=True)
    question_text = Column(Text, nullable=False)
    category_id = Column(Integer, ForeignKey("question_category.category_id"), nullable=False)

    category = relationship("QuestionCategory", back_populates="questions")

class QuestionCategory(Base):
    __tablename__ = "question_category"
    category_id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String(255), nullable=False, unique=True)

    questions = relationship("Question", back_populates="category")

class Recommendation(Base):
    __tablename__ = "recommendation"
    recommend_id = Column(Integer, primary_key=True, index=True)
    action_recommend = Column(String(255))
    recommend_detail = Column(Text)
    color_id = Column(Integer, ForeignKey("color.color_id"))

    color = relationship("Color")

class Color(Base):
    __tablename__ = "color"
    color_id = Column(Integer, primary_key=True, index=True)
    color_name = Column(String(255), unique=True)
    
    records = relationship("DailyRecord", back_populates="color")
    recommendations = relationship("Recommendation", back_populates="color")
    # Lantanとの関連がなくなったため、下の行は不要
    # lantans = relationship("Lantan", back_populates="color")

class Lantan(Base):
    __tablename__ = "lantan"
    lantan_id = Column(Integer, primary_key=True, index=True)
    released_at = Column(DateTime, server_default=func.now())
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False)
    
    # 【修正】color_idの代わりにlantan_color列を追加
    lantan_color = Column(Integer)

    # 【修正】Colorテーブルとの関連を削除
    user = relationship("User", back_populates="lantans")
