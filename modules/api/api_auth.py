#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Вспомогательные функции для аутентификации в API КиберНексус.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import os

# Настройки для JWT аутентификации
SECRET_KEY = os.getenv("CYBERNEXUS_API_SECRET", "secret_key_for_development_only")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Схема OAuth2 для получения токена
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Создание JWT токена доступа.
    
    Args:
        data: Данные для включения в токен
        expires_delta: Время жизни токена
        
    Returns:
        Строка с закодированным JWT токеном
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

def decode_token(token: str) -> Dict[str, Any]:
    """
    Декодирование и проверка JWT токена.
    
    Args:
        token: JWT токен
        
    Returns:
        Данные из токена
        
    Raises:
        HTTPException: Если токен недействителен или просрочен
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен доступа истек",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
            headers={"WWW-Authenticate": "Bearer"}
        )

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Получение текущего пользователя из токена.
    Используется как зависимость FastAPI.
    
    Args:
        token: JWT токен из запроса
        
    Returns:
        Данные о текущем пользователе
    """
    payload = decode_token(token)
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительные данные пользователя",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # В данных пользователя можно добавить дополнительную информацию
    # из базы данных пользователей
    user_data = {
        "id": user_id,
        "name": payload.get("name", "Пользователь"),
        "email": payload.get("email", ""),
        "role": payload.get("role", "user")
    }
    
    return user_data

async def get_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Проверка, что текущий пользователь - администратор.
    Используется как зависимость FastAPI.
    
    Args:
        current_user: Данные о текущем пользователе
        
    Returns:
        Данные о текущем пользователе, если он администратор
        
    Raises:
        HTTPException: Если пользователь не администратор
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Операция доступна только администраторам"
        )
    
    return current_user
