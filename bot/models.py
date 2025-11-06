from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, DeclarativeBase

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True)  
    timezone_offset = Column(Integer, nullable=True)           

    habits = relationship("Habit", back_populates="user")

class Habit(Base):
    __tablename__ = 'habits'

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False) 
    name = Column(String(255), nullable=False)                         
    is_active = Column(Boolean, default=True)                         
    reminder_config = Column(JSONB, nullable=False)                    
    last_reminded_at = Column(DateTime(timezone=True))                  
    next_reminder_datetime_utc = Column(DateTime(timezone=True))         

    completions = relationship("HabitCompletion", back_populates="habit")
    user = relationship("User", back_populates="habits")

class HabitCompletion(Base):
    __tablename__ = 'habit_completions'

    id = Column(Integer, primary_key=True)
    habit_id = Column(Integer, ForeignKey('habits.id'), nullable=False) 
    completed_at = Column(DateTime(timezone=True), nullable=False)      

    habit = relationship("Habit", back_populates="completions")
