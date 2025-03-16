#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API-эндпоинты для механизма обратной связи базы знаний КиберНексус
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Path
from typing import List, Dict, Any, Optional
import datetime

# Импортируем классы из модуля обратной связи
from .feedback_models import (
    FeedbackItem, Comment, Suggestion, ErrorReport, FeatureRequest,
    FeedbackType, FeedbackStatus, FeedbackPriority, create_feedback_item
)
from .feedback_accessor import FeedbackAccessor

# Импортируем функции аутентификации из API-модуля
# (предположительно они расположены в api_auth.py)
from modules.api.api_auth import get_current_user, get_admin_user

# Создаем роутер для эндпоинтов обратной связи
router = APIRouter(
    prefix="/api/feedback",
    tags=["feedback"],
    responses={404: {"description": "Not found"}},
)

# Функция для получения экземпляра FeedbackAccessor
def get_feedback_accessor():
    """
    Создает и возвращает экземпляр FeedbackAccessor.
    Используется как зависимость FastAPI.
    """
    # Здесь можно настроить параметры в зависимости от конфигурации
    accessor = FeedbackAccessor(storage_type="sqlite", path="data/feedback.db")
    try:
        yield accessor
    finally:
        accessor.close()


@router.post("/", response_model=Dict[str, Any])
async def create_feedback(
    feedback_data: Dict[str, Any],
    accessor: FeedbackAccessor = Depends(get_feedback_accessor),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Создание новой обратной связи.
    
    - **feedback_data**: Данные обратной связи
    """
    # Добавляем информацию о пользователе
    feedback_data["user_id"] = current_user.get("id")
    feedback_data["user_name"] = current_user.get("name")
    feedback_data["user_email"] = current_user.get("email")
    
    # Добавляем дату создания
    feedback_data["created_at"] = datetime.datetime.now().isoformat()
    
    # Создаем запись обратной связи
    feedback_id = accessor.add_feedback(feedback_data)
    
    if feedback_id < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось создать обратную связь"
        )
    
    return {"id": feedback_id, "status": "success", "message": "Обратная связь успешно создана"}


@router.get("/", response_model=List[Dict[str, Any]])
async def get_feedback_list(
    type: Optional[str] = Query(None, description="Тип обратной связи"),
    status: Optional[str] = Query(None, description="Статус обратной связи"),
    entity_type: Optional[str] = Query(None, description="Тип сущности"),
    entity_id: Optional[str] = Query(None, description="ID сущности"),
    user_id: Optional[str] = Query(None, description="ID пользователя"),
    tags: Optional[List[str]] = Query(None, description="Теги для фильтрации"),
    limit: int = Query(100, description="Максимальное количество результатов"),
    offset: int = Query(0, description="Смещение для пагинации"),
    sort_by: str = Query("created_at", description="Поле для сортировки"),
    sort_order: str = Query("desc", description="Порядок сортировки (asc/desc)"),
    accessor: FeedbackAccessor = Depends(get_feedback_accessor),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Получение списка обратной связи с возможностью фильтрации и сортировки.
    """
    # Получаем список обратной связи
    feedback_items = accessor.get_feedback_list(
        feedback_type=type,
        status=status,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        tags=tags,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # Преобразуем объекты в словари
    return [item.to_dict() for item in feedback_items]


@router.get("/{feedback_id}", response_model=Dict[str, Any])
async def get_feedback_by_id(
    feedback_id: int = Path(..., description="ID обратной связи"),
    accessor: FeedbackAccessor = Depends(get_feedback_accessor),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Получение обратной связи по ID.
    
    - **feedback_id**: ID обратной связи
    """
    feedback_item = accessor.get_feedback(feedback_id)
    
    if not feedback_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Обратная связь с ID {feedback_id} не найдена"
        )
    
    return feedback_item.to_dict()


@router.put("/{feedback_id}", response_model=Dict[str, Any])
async def update_feedback(
    feedback_id: int = Path(..., description="ID обратной связи"),
    update_data: Dict[str, Any] = Body(..., description="Данные для обновления"),
    accessor: FeedbackAccessor = Depends(get_feedback_accessor),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Обновление существующей обратной связи.
    
    - **feedback_id**: ID обратной связи
    - **update_data**: Данные для обновления
    """
    # Проверяем существование обратной связи
    feedback_item = accessor.get_feedback(feedback_id)
    
    if not feedback_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Обратная связь с ID {feedback_id} не найдена"
        )
    
    # Проверяем права доступа (только администратор или автор может обновлять)
    is_admin = current_user.get("role") == "admin"
    is_author = current_user.get("id") == feedback_item.user_id
    
    if not (is_admin or is_author):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав для обновления этой обратной связи"
        )
    
    # Обновляем обратную связь
    success = accessor.update_feedback(
        feedback_id, 
        update_data, 
        changed_by=current_user.get("id")
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось обновить обратную связь"
        )
    
    return {"status": "success", "message": "Обратная связь успешно обновлена"}


@router.delete("/{feedback_id}", response_model=Dict[str, Any])
async def delete_feedback(
    feedback_id: int = Path(..., description="ID обратной связи"),
    accessor: FeedbackAccessor = Depends(get_feedback_accessor),
    admin_user: Dict[str, Any] = Depends(get_admin_user)  # Только администратор может удалять
):
    """
    Удаление обратной связи по ID.
    
    - **feedback_id**: ID обратной связи
    """
    # Проверяем существование обратной связи
    feedback_item = accessor.get_feedback(feedback_id)
    
    if not feedback_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Обратная связь с ID {feedback_id} не найдена"
        )
    
    # Удаляем обратную связь
    success = accessor.delete_feedback(feedback_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось удалить обратную связь"
        )
    
    return {"status": "success", "message": "Обратная связь успешно удалена"}


@router.post("/{feedback_id}/comments", response_model=Dict[str, Any])
async def add_comment(
    feedback_id: int = Path(..., description="ID обратной связи"),
    content: str = Body(..., description="Содержание комментария"),
    accessor: FeedbackAccessor = Depends(get_feedback_accessor),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Добавление комментария к обратной связи.
    
    - **feedback_id**: ID обратной связи
    - **content**: Содержание комментария
    """
    # Проверяем существование обратной связи
    feedback_item = accessor.get_feedback(feedback_id)
    
    if not feedback_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Обратная связь с ID {feedback_id} не найдена"
        )
    
    # Добавляем комментарий
    comment_id = accessor.add_comment(
        feedback_id,
        current_user.get("id"),
        current_user.get("name"),
        content
    )
    
    if comment_id < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось добавить комментарий"
        )
    
    return {"id": comment_id, "status": "success", "message": "Комментарий успешно добавлен"}


@router.get("/{feedback_id}/comments", response_model=List[Dict[str, Any]])
async def get_comments(
    feedback_id: int = Path(..., description="ID обратной связи"),
    accessor: FeedbackAccessor = Depends(get_feedback_accessor),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Получение комментариев к обратной связи.
    
    - **feedback_id**: ID обратной связи
    """
    # Проверяем существование обратной связи
    feedback_item = accessor.get_feedback(feedback_id)
    
    if not feedback_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Обратная связь с ID {feedback_id} не найдена"
        )
    
    # Получаем комментарии
    comments = accessor.get_comments(feedback_id)
    
    return comments


@router.get("/{feedback_id}/history", response_model=List[Dict[str, Any]])
async def get_status_history(
    feedback_id: int = Path(..., description="ID обратной связи"),
    accessor: FeedbackAccessor = Depends(get_feedback_accessor),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Получение истории изменений статуса обратной связи.
    
    - **feedback_id**: ID обратной связи
    """
    # Проверяем существование обратной связи
    feedback_item = accessor.get_feedback(feedback_id)
    
    if not feedback_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Обратная связь с ID {feedback_id} не найдена"
        )
    
    # Получаем историю изменений статуса
    history = accessor.get_status_history(feedback_id)
    
    return history


@router.post("/{feedback_id}/tags/{tag}", response_model=Dict[str, Any])
async def add_tag(
    feedback_id: int = Path(..., description="ID обратной связи"),
    tag: str = Path(..., description="Тег для добавления"),
    accessor: FeedbackAccessor = Depends(get_feedback_accessor),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Добавление тега к обратной связи.
    
    - **feedback_id**: ID обратной связи
    - **tag**: Тег для добавления
    """
    # Проверяем существование обратной связи
    feedback_item = accessor.get_feedback(feedback_id)
    
    if not feedback_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Обратная связь с ID {feedback_id} не найдена"
        )
    
    # Проверяем права доступа (только администратор или автор может добавлять теги)
    is_admin = current_user.get("role") == "admin"
    is_author = current_user.get("id") == feedback_item.user_id
    
    if not (is_admin or is_author):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав для добавления тегов к этой обратной связи"
        )
    
    # Добавляем тег
    success = accessor.add_tag(feedback_id, tag)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось добавить тег"
        )
    
    return {"status": "success", "message": "Тег успешно добавлен"}


@router.delete("/{feedback_id}/tags/{tag}", response_model=Dict[str, Any])
async def remove_tag(
    feedback_id: int = Path(..., description="ID обратной связи"),
    tag: str = Path(..., description="Тег для удаления"),
    accessor: FeedbackAccessor = Depends(get_feedback_accessor),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Удаление тега из обратной связи.
    
    - **feedback_id**: ID обратной связи
    - **tag**: Тег для удаления
    """
    # Проверяем существование обратной связи
    feedback_item = accessor.get_feedback(feedback_id)
    
    if not feedback_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Обратная связь с ID {feedback_id} не найдена"
        )
    
    # Проверяем права доступа (только администратор или автор может удалять теги)
    is_admin = current_user.get("role") == "admin"
    is_author = current_user.get("id") == feedback_item.user_id
    
    if not (is_admin or is_author):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав для удаления тегов из этой обратной связи"
        )
    
    # Удаляем тег
    success = accessor.remove_tag(feedback_id, tag)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось удалить тег"
        )
    
    return {"status": "success", "message": "Тег успешно удален"}


@router.post("/{feedback_id}/upvote", response_model=Dict[str, Any])
async def upvote_feedback(
    feedback_id: int = Path(..., description="ID обратной связи"),
    accessor: FeedbackAccessor = Depends(get_feedback_accessor),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Голосование за обратную связь.
    
    - **feedback_id**: ID обратной связи
    """
    # Проверяем существование обратной связи
    feedback_item = accessor.get_feedback(feedback_id)
    
    if not feedback_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Обратная связь с ID {feedback_id} не найдена"
        )
    
    # Увеличиваем счетчик голосов
    success = accessor.upvote_feedback(feedback_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось проголосовать за обратную связь"
        )
    
    return {"status": "success", "message": "Голос успешно учтен"}


@router.get("/statistics", response_model=Dict[str, Any])
async def get_statistics(
    accessor: FeedbackAccessor = Depends(get_feedback_accessor),
    admin_user: Dict[str, Any] = Depends(get_admin_user)  # Только администратор может получать статистику
):
    """
    Получение статистики по обратной связи.
    """
    # Получаем статистику
    statistics = accessor.get_statistics()
    
    return statistics


@router.post("/export", response_model=Dict[str, Any])
async def export_feedback(
    output_path: str = Body(..., description="Путь к файлу для экспорта"),
    accessor: FeedbackAccessor = Depends(get_feedback_accessor),
    admin_user: Dict[str, Any] = Depends(get_admin_user)  # Только администратор может экспортировать
):
    """
    Экспорт данных обратной связи в JSON-файл.
    
    - **output_path**: Путь к файлу для экспорта
    """
    try:
        accessor.export_to_json(output_path)
        return {"status": "success", "message": f"Данные обратной связи экспортированы в {output_path}"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при экспорте данных: {str(e)}"
        )


@router.post("/import", response_model=Dict[str, Any])
async def import_feedback(
    input_path: str = Body(..., description="Путь к файлу для импорта"),
    accessor: FeedbackAccessor = Depends(get_feedback_accessor),
    admin_user: Dict[str, Any] = Depends(get_admin_user)  # Только администратор может импортировать
):
    """
    Импорт данных обратной связи из JSON-файла.
    
    - **input_path**: Путь к файлу для импорта
    """
    try:
        accessor.import_from_json(input_path)
        return {"status": "success", "message": f"Данные обратной связи импортированы из {input_path}"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при импорте данных: {str(e)}"
        )


@router.get("/search", response_model=List[Dict[str, Any]])
async def search_feedback(
    query: str = Query(..., description="Поисковый запрос"),
    limit: int = Query(20, description="Максимальное количество результатов"),
    accessor: FeedbackAccessor = Depends(get_feedback_accessor),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Полнотекстовый поиск по обратной связи.
    
    - **query**: Поисковый запрос
    - **limit**: Максимальное количество результатов
    """
    # Выполняем поиск
    feedback_items = accessor.search_feedback(query, limit)
    
    # Преобразуем объекты в словари
    return [item.to_dict() for item in feedback_items]
