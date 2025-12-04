import sys
import os

from habit.calculate_percentage import calculate_completion_percentage
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'bot'))
from models import Habit

async def format_habit_info_for_deletion(habit: Habit) -> str:

    percentage = await calculate_completion_percentage(habit.id)


    config = habit.reminder_config
    habit_type = config.get("type", "неизвестно")

    habit_info_lines = [
        f"Название: <b>{habit.name}</b>"
    ]

    if habit_type == "by_days":
        habit_info_lines.append(f"Тип: повторение каждые {config.get('num_days', '?')} день(а)")
        habit_info_lines.append(f"Время напоминания: {config.get('time_to_check', '?')}")

    elif habit_type == "by_week":
        period = config.get('period_weeks', '?')
        days = config.get('weekdays', [])
        time_check = config.get('time_to_check', '?')
        days_str = ", ".join(days) if days else "?"
        habit_info_lines.append(f"Тип: повторение каждые {period} недель(и)")
        habit_info_lines.append(f"Дни напоминания: {days_str}")
        habit_info_lines.append(f"Время напоминания: {time_check}")

    status = "✅ Активна" if habit.is_active else "❌ Неактивна"
    habit_info_lines.append(f"Статус: {status}")
    habit_info_lines.append(f"Процент выполнения: {percentage}%")

    habit_info = "\n".join(habit_info_lines) + "\n\n"
    return habit_info