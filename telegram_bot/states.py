"""FSM state groups for multi-step conversations (aiogram 3 StatesGroup)."""
from aiogram.fsm.state import State, StatesGroup


class HabitCreate(StatesGroup):
    name = State()
    frequency = State()
    icon = State()


class TodoCreate(StatesGroup):
    title = State()
    priority = State()
    due_date = State()


class TransactionCreate(StatesGroup):
    type = State()
    amount = State()
    category = State()
    date = State()
    description = State()


class ReminderCreate(StatesGroup):
    title = State()
    when = State()
    recurrence = State()
