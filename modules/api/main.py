#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Основной модуль API для базы знаний КиберНексус.
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List
import datetime

# Импортируем функции аутентификации
from .api_auth import (
    create_access_token, 
    get_current_user, 
    get_admin_user, 
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# Импортируем роутер модуля обратной связи
from modules.feedback.feedback_api import router as feedback_router

# Создаем экземпляр приложения FastAPI
app = FastAPI(
    title="КиберНексус API",
    description="API для базы знаний по кибербезопасности компании КиберНексус",
    version="1.0.0"
)

# Настройка CORS для работы с фронтендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшне рекомендуется указывать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутер модуля обратной связи
app.include_router(feedback_router)

@app.post("/token", response_model=Dict[str, str])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()) -> Dict[str, str]:
    """
    Аутентификация пользователя и получение JWT токена.
    """
    # Здесь должна быть проверка пользователя в базе данных
    # В простом варианте - проверка логина/пароля
    # Например: user = authenticate_user(form_data.username, form_data.password)
    
    # Для демонстрации используем простую проверку
    if form_data.username == "admin" and form_data.password == "password":
        user_data = {
            "sub": "admin",
            "name": "Администратор",
            "email": "admin@cybernexus.com",
            "role": "admin"
        }
    elif form_data.username == "user" and form_data.password == "password":
        user_data = {
            "sub": "user1",
            "name": "Пользователь",
            "email": "user@cybernexus.com",
            "role": "user"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Создаем JWT токен
    access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data=user_data, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
async def root():
    """
    Корневой эндпоинт API.
    """
    return {
        "message": "КиберНексус API",
        "version": "1.0.0",
        "documentation": "/docs"
    }

@app.get("/users/me", response_model=Dict[str, Any])
async def read_users_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Получение информации о текущем пользователе.
    """
    return current_user

# Здесь можно добавить дополнительные маршруты для API базы знаний
