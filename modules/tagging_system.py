#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Система тегирования контента в базе знаний по кибербезопасности
Позволяет добавлять теги к элементам базы знаний, управлять тегами и осуществлять поиск по тегам
"""

import json
import os
import sqlite3
import re
from typing import List, Dict, Any, Set, Tuple, Optional
from collections import Counter


class TaggingSystem:
    """Класс для работы с системой тегирования базы знаний"""
    
    def __init__(self, knowledge_base_path: str, storage_type: str = "json"):
        """
        Инициализация системы тегирования
        
        Args:
            knowledge_base_path: Путь к файлу базы знаний
            storage_type: Тип хранилища ("json" или "sqlite")
        """
        self.knowledge_base_path = knowledge_base_path
        self.storage_type = storage_type.lower()
        self.tags_file = os.path.join(os.path.dirname(knowledge_base_path), "tags.json")
        
        # Структура тегов: {tag_name: {category: str, description: str, color: str}}
        self.tags_metadata = {}
        
        # Структура привязки тегов: {entity_id: {entity_type: str, tags: List[str]}}
        self.entity_tags = {}
        
        # Загружаем существующие теги
        self._load_tags()
    
    def _load_tags(self):
        """Загрузка данных о тегах"""
        try:
            if os.path.exists(self.tags_file):
                with open(self.tags_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.tags_metadata = data.get("tags_metadata", {})
                    self.entity_tags = data.get("entity_tags", {})
                print(f"Загружено {len(self.tags_metadata)} тегов для {len(self.entity_tags)} элементов")
            else:
                print("Файл тегов не найден, создаем новую систему тегирования")
        except Exception as e:
            print(f"Ошибка при загрузке тегов: {e}")
            self.tags_metadata = {}
            self.entity_tags = {}
    
    def _save_tags(self):
        """Сохранение данных о тегах"""
        try:
            data = {
                "tags_metadata": self.tags_metadata,
                "entity_tags": self.entity_tags
            }
            os.makedirs(os.path.dirname(os.path.abspath(self.tags_file)), exist_ok=True)
            with open(self.tags_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Теги сохранены в {self.tags_file}")
        except Exception as e:
            print(f"Ошибка при сохранении тегов: {e}")
    
    def add_tag(self, tag_name: str, category: str = "general", description: str = "", color: str = "#1E90FF"):
        """
        Добавление нового тега
        
        Args:
            tag_name: Название тега
            category: Категория тега (general, threat, protection, compliance, etc.)
            description: Описание тега
            color: Цвет тега в формате HEX
        """
        # Нормализуем имя тега
        tag_name = tag_name.lower().strip()
        
        if tag_name in self.tags_metadata:
            print(f"Тег '{tag_name}' уже существует, обновляем метаданные")
        
        # Проверяем формат цвета
        if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
            print(f"Неверный формат цвета: {color}, используем стандартный")
            color = "#1E90FF"  # Стандартный синий цвет
        
        # Добавляем тег
        self.tags_metadata[tag_name] = {
            "category": category,
            "description": description,
            "color": color
        }
        
        self._save_tags()
        print(f"Тег '{tag_name}' добавлен")
    
    def remove_tag(self, tag_name: str):
        """
        Удаление тега
        
        Args:
            tag_name: Название тега
        """
        tag_name = tag_name.lower().strip()
        
        if tag_name not in self.tags_metadata:
            print(f"Тег '{tag_name}' не найден")
            return
        
        # Удаляем метаданные тега
        del self.tags_metadata[tag_name]
        
        # Удаляем привязки тега к элементам
        for entity_id in self.entity_tags:
            if "tags" in self.entity_tags[entity_id] and tag_name in self.entity_tags[entity_id]["tags"]:
                self.entity_tags[entity_id]["tags"].remove(tag_name)
        
        self._save_tags()
        print(f"Тег '{tag_name}' удален")
    
    def get_tags(self, category: str = None) -> Dict[str, Dict[str, Any]]:
        """
        Получение списка тегов
        
        Args:
            category: Опциональный фильтр по категории
            
        Returns:
            Словарь тегов с их метаданными
        """
        if category is None:
            return self.tags_metadata
        else:
            return {tag: data for tag, data in self.tags_metadata.items() 
                   if data.get("category") == category}
    
    def tag_entity(self, entity_id: str, entity_type: str, tags: List[str]):
        """
        Добавление тегов к элементу базы знаний
        
        Args:
            entity_id: Идентификатор элемента
            entity_type: Тип элемента (term, product, threat, etc.)
            tags: Список тегов для добавления
        """
        # Нормализуем теги
        normalized_tags = [tag.lower().strip() for tag in tags]
        
        # Проверяем существование тегов и создаем отсутствующие
        for tag in normalized_tags:
            if tag not in self.tags_metadata:
                self.add_tag(tag)
        
        # Обновляем привязки тегов
        if entity_id not in self.entity_tags:
            self.entity_tags[entity_id] = {
                "entity_type": entity_type,
                "tags": normalized_tags
            }
        else:
            # Сохраняем тип элемента
            self.entity_tags[entity_id]["entity_type"] = entity_type
            
            # Обновляем список тегов
            if "tags" not in self.entity_tags[entity_id]:
                self.entity_tags[entity_id]["tags"] = normalized_tags
            else:
                # Добавляем новые теги к существующим
                existing_tags = set(self.entity_tags[entity_id]["tags"])
                existing_tags.update(normalized_tags)
                self.entity_tags[entity_id]["tags"] = list(existing_tags)
        
        self._save_tags()
        print(f"Добавлены теги для {entity_id}: {', '.join(normalized_tags)}")
    
    def untag_entity(self, entity_id: str, tags: List[str] = None):
        """
        Удаление тегов у элемента базы знаний
        
        Args:
            entity_id: Идентификатор элемента
            tags: Список тегов для удаления или None для удаления всех тегов
        """
        if entity_id not in self.entity_tags:
            print(f"Элемент '{entity_id}' не найден")
            return
        
        if tags is None:
            # Удаляем все теги
            if "tags" in self.entity_tags[entity_id]:
                del self.entity_tags[entity_id]["tags"]
            print(f"Удалены все теги для {entity_id}")
        else:
            # Нормализуем теги
            normalized_tags = [tag.lower().strip() for tag in tags]
            
            # Удаляем указанные теги
            if "tags" in self.entity_tags[entity_id]:
                self.entity_tags[entity_id]["tags"] = [
                    tag for tag in self.entity_tags[entity_id]["tags"]
                    if tag not in normalized_tags
                ]
                print(f"Удалены теги для {entity_id}: {', '.join(normalized_tags)}")
        
        # Если у элемента не осталось тегов и типа, удаляем его из системы
        if not self.entity_tags[entity_id].get("tags") and not self.entity_tags[entity_id].get("entity_type"):
            del self.entity_tags[entity_id]
        
        self._save_tags()
    
    def get_entity_tags(self, entity_id: str) -> List[str]:
        """
        Получение списка тегов для элемента
        
        Args:
            entity_id: Идентификатор элемента
            
        Returns:
            Список тегов элемента
        """
        if entity_id not in self.entity_tags:
            return []
        
        return self.entity_tags[entity_id].get("tags", [])
    
    def find_entities_by_tags(self, tags: List[str], match_all: bool = False, entity_type: str = None) -> List[str]:
        """
        Поиск элементов по тегам
        
        Args:
            tags: Список тегов для поиска
            match_all: True для поиска элементов со всеми указанными тегами, 
                       False для поиска элементов с любым из указанных тегов
            entity_type: Опциональный фильтр по типу элемента
            
        Returns:
            Список идентификаторов элементов, соответствующих критериям поиска
        """
        normalized_tags = set(tag.lower().strip() for tag in tags)
        result = []
        
        for entity_id, entity_data in self.entity_tags.items():
            # Фильтр по типу элемента
            if entity_type is not None and entity_data.get("entity_type") != entity_type:
                continue
            
            entity_tags = set(entity_data.get("tags", []))
            
            if match_all:
                # Элемент должен иметь все указанные теги
                if normalized_tags.issubset(entity_tags):
                    result.append(entity_id)
            else:
                # Элемент должен иметь хотя бы один из указанных тегов
                if normalized_tags.intersection(entity_tags):
                    result.append(entity_id)
        
        return result
    
    def get_related_tags(self, tag_name: str, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Получение связанных тегов, которые часто используются вместе с указанным
        
        Args:
            tag_name: Название тега
            limit: Максимальное количество связанных тегов
            
        Returns:
            Список кортежей (tag_name, count) с названием тега и количеством совместных упоминаний
        """
        tag_name = tag_name.lower().strip()
        
        # Находим все элементы с указанным тегом
        entities_with_tag = self.find_entities_by_tags([tag_name])
        
        # Собираем все теги этих элементов
        related_tags = Counter()
        for entity_id in entities_with_tag:
            entity_tags = self.get_entity_tags(entity_id)
            for tag in entity_tags:
                if tag != tag_name:  # Исключаем исходный тег
                    related_tags[tag] += 1
        
        # Возвращаем самые часто встречающиеся теги
        return related_tags.most_common(limit)
    
    def get_tag_statistics(self) -> Dict[str, Any]:
        """
        Получение статистики по использованию тегов
        
        Returns:
            Словарь со статистикой
        """
        # Счетчик использования тегов
        tag_usage = Counter()
        
        # Счетчик использования категорий
        category_usage = Counter()
        
        # Общее количество элементов с тегами
        total_tagged_entities = 0
        
        # Собираем статистику
        for entity_id, entity_data in self.entity_tags.items():
            entity_tags = entity_data.get("tags", [])
            if entity_tags:
                total_tagged_entities += 1
                
                for tag in entity_tags:
                    tag_usage[tag] += 1
                    
                    # Увеличиваем счетчик для категории тега
                    if tag in self.tags_metadata:
                        category = self.tags_metadata[tag].get("category", "general")
                        category_usage[category] += 1
        
        # Формируем результат
        result = {
            "total_tags": len(self.tags_metadata),
            "total_tagged_entities": total_tagged_entities,
            "most_used_tags": tag_usage.most_common(10),
            "category_usage": dict(category_usage),
            "tags_per_category": {
                category: len([tag for tag, data in self.tags_metadata.items() 
                              if data.get("category") == category])
                for category in set(data.get("category", "general") for data in self.tags_metadata.values())
            }
        }
        
        return result
    
    def suggest_tags(self, entity_id: str, num_suggestions: int = 5) -> List[str]:
        """
        Предложение тегов для элемента на основе анализа похожих элементов
        
        Args:
            entity_id: Идентификатор элемента
            num_suggestions: Количество предлагаемых тегов
            
        Returns:
            Список предлагаемых тегов
        """
        if entity_id not in self.entity_tags:
            print(f"Элемент '{entity_id}' не найден")
            return []
        
        entity_type = self.entity_tags[entity_id].get("entity_type")
        current_tags = set(self.entity_tags[entity_id].get("tags", []))
        
        # Находим элементы того же типа с похожими тегами
        similar_entities = []
        for eid, edata in self.entity_tags.items():
            if eid != entity_id and edata.get("entity_type") == entity_type:
                etags = set(edata.get("tags", []))
                # Вычисляем сходство как пересечение множеств тегов
                if current_tags and etags:
                    similarity = len(current_tags.intersection(etags)) / len(current_tags.union(etags))
                    if similarity > 0:
                        similar_entities.append((eid, similarity))
        
        # Сортируем по убыванию сходства
        similar_entities.sort(key=lambda x: x[1], reverse=True)
        
        # Собираем теги из похожих элементов
        suggested_tags = Counter()
        for eid, similarity in similar_entities[:10]:  # Рассматриваем до 10 похожих элементов
            etags = self.entity_tags[eid].get("tags", [])
            for tag in etags:
                if tag not in current_tags:
                    suggested_tags[tag] += similarity  # Учитываем сходство при подсчете
        
        # Возвращаем наиболее релевантные теги
        return [tag for tag, _ in suggested_tags.most_common(num_suggestions)]
    
    def export_tags(self, output_path: str = "exported_tags.json"):
        """
        Экспорт системы тегирования в отдельный файл
        
        Args:
            output_path: Путь для сохранения файла
            
        Returns:
            Путь к сохраненному файлу
        """
        try:
            data = {
                "tags_metadata": self.tags_metadata,
                "entity_tags": self.entity_tags,
                "statistics": self.get_tag_statistics()
            }
            
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"Теги экспортированы в {output_path}")
            return output_path
        except Exception as e:
            print(f"Ошибка при экспорте тегов: {e}")
            return None
    
    def import_tags(self, input_path: str):
        """
        Импорт системы тегирования из файла
        
        Args:
            input_path: Путь к файлу с тегами
            
        Returns:
            True в случае успешного импорта, иначе False
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.tags_metadata = data.get("tags_metadata", {})
            self.entity_tags = data.get("entity_tags", {})
            
            self._save_tags()
            print(f"Теги импортированы из {input_path}")
            return True
        except Exception as e:
            print(f"Ошибка при импорте тегов: {e}")
            return False


# Пример использования
if __name__ == "__main__":
    # Создаем систему тегирования
    tagging = TaggingSystem("knowledge_base.json", "json")
    
    # Добавляем несколько категорий тегов
    for category, color in [
        ("threat", "#FF6347"),  # Томатный
        ("protection", "#32CD32"),  # Зеленый
        ("compliance", "#FFD700"),  # Золотой
        ("technology", "#1E90FF"),  # Синий
        ("attack_vector", "#FF69B4")  # Розовый
    ]:
        # Добавляем категорию (создаем тег с именем категории)
        tagging.add_tag(category, category, f"Категория: {category}", color)
    
    # Добавляем несколько тегов для терминов
    tagging.tag_entity("cybersecurity", "term", ["protection", "technology", "security"])
    tagging.tag_entity("information_security", "term", ["protection", "compliance", "security"])
    
    # Добавляем теги для продукта
    tagging.tag_entity("intellectshield", "product", ["protection", "technology", "ai", "anomaly_detection"])
    
    # Получаем статистику использования тегов
    stats = tagging.get_tag_statistics()
    print("\nСтатистика использования тегов:")
    print(f"Всего тегов: {stats['total_tags']}")
    print(f"Элементов с тегами: {stats['total_tagged_entities']}")
    print("Наиболее используемые теги:")
    for tag, count in stats['most_used_tags']:
        print(f"  - {tag}: {count}")
    
    # Экспортируем теги
    os.makedirs("exports", exist_ok=True)
    tagging.export_tags("exports/tags_export.json")
