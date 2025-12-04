import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from io import BytesIO
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone, timedelta

from habit.calculate_percentage import calculate_completion_percentage, calculate_weekly_completion_percentage

import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'bot'))
from models import Habit


async def generate_statistic_image(user_id: int, session: AsyncSession) -> BytesIO:

    result = await session.execute(
    select(Habit)
    .options(selectinload(Habit.completions)) 
    .where(Habit.user_id == user_id, Habit.is_active.is_(True))
)
    habits = result.scalars().all()

    if not habits:
        plt.figure(figsize=(6, 3))
        plt.text(0.5, 0.5, 'Нет активных привычек.', ha='center', va='center', fontsize=14)
        plt.axis('off')
    else:
        habits = sorted(habits, key=lambda h: h.id)

        percentages = []
        names = []

        for habit in habits:
            percentage = await calculate_completion_percentage(habit.id)
            percentages.append(percentage)
            names.append(habit.name)

        plt.figure(figsize=(8, max(4, len(names) * 0.6)))
        
        bars = plt.barh(names, percentages, color=((101/255, 119/255, 173/255)))  

        for bar, pct in zip(bars, percentages):
            width = bar.get_width()
            plt.text(width + 1, bar.get_y() + bar.get_height()/2,
                     f'{pct:.0f}%', va='center', fontsize=10)

        plt.xlim(0, 100)
        plt.xlabel('Прогресс (%)', fontsize=12)
        plt.title('Ваш прогресс по привычкам', fontsize=14, pad=20)
        plt.gca().set_facecolor((244/255, 244/255, 249/255))  
        plt.grid(axis='x', color='grey', linestyle='--', linewidth=0.5, alpha=0.7)
        plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return buf


async def generate_weekly_statistic_image(user_id: int, session: AsyncSession) -> BytesIO:

    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=7)
    
    result = await session.execute(
        select(Habit)
        .options(selectinload(Habit.completions)) 
        .where(Habit.user_id == user_id, Habit.is_active.is_(True))
    )
    habits = result.scalars().all()

    if not habits:
        plt.figure(figsize=(6, 3))
        plt.text(0.5, 0.5, 'Нет активных привычек.', ha='center', va='center', fontsize=14)
        plt.axis('off')
    else:
        habits = sorted(habits, key=lambda h: h.id)

        percentages = []
        names = []
        changes = []

        for habit in habits:
            current_percentage = await calculate_completion_percentage(habit.id)
            past_percentage = await calculate_weekly_completion_percentage(habit.id, start_date)
            change_percentage = current_percentage - past_percentage
            
            percentages.append(current_percentage)
            names.append(habit.name)
            changes.append(change_percentage)

        plt.figure(figsize=(8, max(4, len(names) * 0.6)))
        
        bars = plt.barh(names, percentages, color=((101/255, 119/255, 173/255)))  

        for bar, pct, change in zip(bars, percentages, changes):
            width = bar.get_width()
            plt.text(width + 1, bar.get_y() + bar.get_height()/2,
                     f'{pct:.0f}%', va='center', fontsize=10)
            
            change_symbol = "+" if change > 0 else ""
            plt.text(width + 8, bar.get_y() + bar.get_height()/2,
                     f'({change_symbol}{change:.0f}%)', va='center', fontsize=9, 
                     color=((101/255, 119/255, 173/255)) if change > 0 else 'red')

        plt.xlim(0, 100)
        plt.xlabel('Прогресс (%)', fontsize=12)

        plt.title('Ваш прогресс по привычкам (изменение за неделю)', fontsize=14, pad=20)
        plt.gca().set_facecolor((244/255, 244/255, 249/255))  
        plt.grid(axis='x', color='grey', linestyle='--', linewidth=0.5, alpha=0.7)
        plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return buf
