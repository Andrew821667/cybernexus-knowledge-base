#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль автоматического обогащения базы знаний по кибербезопасности

Модуль предназначен для автоматического сбора и обработки информации об угрозах
кибербезопасности из различных источников и её интеграции в базу знаний компании.

Основные функции:
1. Сбор данных из различных источников (API, RSS-ленты, веб-страницы)
2. Обработка и классификация данных с использованием AI
3. Интеграция новых данных в базу знаний
4. Планирование и запуск задач по обогащению базы знаний
"""

import os
import json
import re
import time
import logging
import requests
import datetime
import hashlib
import feedparser
import sqlite3
from typing import List, Dict, Any, Optional, Union, Tuple
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import xml.etree.ElementTree as ET

# Импортируем основной класс для работы с базой знаний
import sys
sys.path.append('../..')
from knowledge_base_accessor import KnowledgeBaseAccessor


# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("auto_enrichment.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class ThreatIntelSource:
    """Базовый класс для источников данных об угрозах"""
    
    def __init__(self, name: str, source_type: str, config: Dict[str, Any]):
        """
        Инициализация источника данных
        
        Args:
            name: Название источника
            source_type: Тип источника (api, rss, webpage)
            config: Конфигурация источника
        """
        self.name = name
        self.source_type = source_type
        self.config = config
        self.last_update = None
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        """
        Получение данных из источника
        
        Returns:
            Список записей с данными
        """
        raise NotImplementedError("Метод должен быть переопределен в дочернем классе")
    
    def _parse_date(self, date_str: str) -> datetime.datetime:
        """
        Преобразование строки даты в объект datetime
        
        Args:
            date_str: Строка с датой
            
        Returns:
            Объект datetime
        """
        # Поддержка различных форматов даты
        formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",  # 2023-01-15T14:30:45.123Z
            "%Y-%m-%dT%H:%M:%SZ",     # 2023-01-15T14:30:45Z
            "%Y-%m-%d %H:%M:%S",      # 2023-01-15 14:30:45
            "%a, %d %b %Y %H:%M:%S %z",  # RSS формат: Wed, 15 Jan 2023 14:30:45 +0000
            "%d %b %Y",               # 15 Jan 2023
            "%Y-%m-%d"                # 2023-01-15
        ]
        
        for fmt in formats:
            try:
                return datetime.datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        logger.warning(f"Не удалось распознать формат даты: {date_str}")
        return datetime.datetime.now()
    
    def _generate_id(self, data: Dict[str, Any]) -> str:
        """
        Генерация уникального идентификатора для записи
        
        Args:
            data: Данные записи
            
        Returns:
            Уникальный идентификатор
        """
        # Создаем строку из заголовка и описания (если они есть)
        content = data.get("title", "") + data.get("description", "")
        # Генерируем MD5-хеш
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _make_request(self, url: str, headers: Dict = None, params: Dict = None) -> requests.Response:
        """
        Выполнение HTTP-запроса с обработкой ошибок и повторными попытками
        
        Args:
            url: URL для запроса
            headers: Заголовки запроса
            params: Параметры запроса
            
        Returns:
            Объект ответа
        """
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, params=params, timeout=10)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                logger.warning(f"Ошибка при выполнении запроса ({attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Экспоненциальная задержка
                else:
                    logger.error(f"Не удалось выполнить запрос после {max_retries} попыток: {url}")
                    raise


class APIThreatSource(ThreatIntelSource):
    """Класс для получения данных через API"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Инициализация источника данных API
        
        Args:
            name: Название источника
            config: Конфигурация источника:
                - url: URL API
                - api_key: Ключ API (если требуется)
                - endpoint: Конечная точка API
                - headers: Дополнительные заголовки
                - params: Параметры запроса
                - response_format: Формат ответа (json, xml)
                - data_path: Путь к данным в ответе
        """
        super().__init__(name, "api", config)
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        """
        Получение данных через API
        
        Returns:
            Список записей с данными
        """
        url = self.config["url"]
        headers = self.config.get("headers", {})
        params = self.config.get("params", {})
        
        # Добавляем API ключ в заголовки или параметры
        if "api_key" in self.config:
            if self.config.get("api_key_in", "header") == "header":
                headers[self.config.get("api_key_name", "X-API-Key")] = self.config["api_key"]
            else:
                params[self.config.get("api_key_name", "api_key")] = self.config["api_key"]
        
        try:
            response = self._make_request(url, headers=headers, params=params)
            
            # Обработка ответа в зависимости от формата
            format_type = self.config.get("response_format", "json")
            
            if format_type == "json":
                data = response.json()
                # Извлекаем данные по указанному пути
                if "data_path" in self.config:
                    path_parts = self.config["data_path"].split(".")
                    for part in path_parts:
                        if isinstance(data, dict) and part in data:
                            data = data[part]
                        else:
                            logger.warning(f"Не удалось найти путь {self.config['data_path']} в ответе")
                            return []
                
                if not isinstance(data, list):
                    logger.warning(f"Ожидался список данных, получено: {type(data)}")
                    return []
                
                # Преобразуем данные в стандартный формат
                result = []
                for item in data:
                    record = {
                        "source": self.name,
                        "source_type": self.source_type,
                        "id": self._generate_id(item),
                        "title": item.get(self.config.get("title_field", "title"), ""),
                        "description": item.get(self.config.get("description_field", "description"), ""),
                        "published": item.get(self.config.get("date_field", "published_at"), datetime.datetime.now().isoformat()),
                        "link": item.get(self.config.get("link_field", "url"), ""),
                        "raw_data": item
                    }
                    
                    # Преобразуем дату в строковый формат, если она не строка
                    if not isinstance(record["published"], str):
                        record["published"] = record["published"].isoformat() if hasattr(record["published"], "isoformat") else str(record["published"])
                    
                    result.append(record)
                
                self.last_update = datetime.datetime.now()
                return result
            
            elif format_type == "xml":
                # Парсинг XML-ответа
                root = ET.fromstring(response.text)
                
                # Настройка пространства имен, если указано
                ns = self.config.get("namespace", "")
                ns_prefix = "{" + ns + "}" if ns else ""
                
                # Путь к записям (items)
                items_path = self.config.get("items_path", "item")
                # Добавляем префикс пространства имен к пути
                items_path = items_path.replace("/", f"/{ns_prefix}")
                
                items = root.findall(f".//{ns_prefix}{items_path}")
                
                result = []
                for item in items:
                    # Функция для получения текста элемента с учетом пространства имен
                    def get_element_text(elem, tag, default=""):
                        element = elem.find(f"{ns_prefix}{tag}")
                        return element.text if element is not None and element.text else default
                    
                    title_field = self.config.get("title_field", "title")
                    desc_field = self.config.get("description_field", "description")
                    date_field = self.config.get("date_field", "pubDate")
                    link_field = self.config.get("link_field", "link")
                    
                    record = {
                        "source": self.name,
                        "source_type": self.source_type,
                        "id": self._generate_id({"title": get_element_text(item, title_field)}),
                        "title": get_element_text(item, title_field),
                        "description": get_element_text(item, desc_field),
                        "published": get_element_text(item, date_field, datetime.datetime.now().isoformat()),
                        "link": get_element_text(item, link_field),
                        "raw_data": ET.tostring(item, encoding='unicode')
                    }
                    
                    result.append(record)
                
                self.last_update = datetime.datetime.now()
                return result
            
            else:
                logger.error(f"Неподдерживаемый формат ответа: {format_type}")
                return []
        
        except Exception as e:
            logger.error(f"Ошибка при получении данных из {self.name}: {e}")
            return []


class RSSFeedSource(ThreatIntelSource):
    """Класс для получения данных из RSS-лент"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Инициализация источника данных RSS
        
        Args:
            name: Название источника
            config: Конфигурация источника:
                - url: URL RSS-ленты
                - filter_keywords: Ключевые слова для фильтрации (опционально)
        """
        super().__init__(name, "rss", config)
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        """
        Получение данных из RSS-ленты
        
        Returns:
            Список записей с данными
        """
        url = self.config["url"]
        
        try:
            # Получаем данные из RSS-ленты
            feed = feedparser.parse(url)
            
            if not feed.entries:
                logger.warning(f"Нет записей в RSS-ленте: {url}")
                return []
            
            # Фильтрация по ключевым словам, если указаны
            filter_keywords = self.config.get("filter_keywords", [])
            
            result = []
            for entry in feed.entries:
                # Проверяем наличие ключевых слов в заголовке или описании
                if filter_keywords:
                    title = entry.get("title", "").lower()
                    summary = entry.get("summary", "").lower()
                    description = entry.get("description", "").lower()
                    content = title + " " + summary + " " + description
                    
                    if not any(keyword.lower() in content for keyword in filter_keywords):
                        continue
                
                # Получаем дату публикации
                published = entry.get("published", entry.get("updated", datetime.datetime.now().isoformat()))
                
                # Преобразуем дату в стандартный формат, если она в виде строки
                if isinstance(published, str):
                    try:
                        published = self._parse_date(published)
                        published = published.isoformat()
                    except Exception as e:
                        logger.warning(f"Ошибка при преобразовании даты: {e}")
                
                record = {
                    "source": self.name,
                    "source_type": self.source_type,
                    "id": entry.get("id", self._generate_id(entry)),
                    "title": entry.get("title", ""),
                    "description": entry.get("summary", entry.get("description", "")),
                    "published": published,
                    "link": entry.get("link", ""),
                    "raw_data": entry
                }
                
                result.append(record)
            
            self.last_update = datetime.datetime.now()
            return result
        
        except Exception as e:
            logger.error(f"Ошибка при получении данных из RSS-ленты {self.name}: {e}")
            return []


class WebPageSource(ThreatIntelSource):
    """Класс для получения данных с веб-страниц"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Инициализация источника данных веб-страницы
        
        Args:
            name: Название источника
            config: Конфигурация источника:
                - url: URL веб-страницы
                - selectors: CSS-селекторы для извлечения данных:
                    - item: Селектор для элементов с данными
                    - title: Селектор для заголовка
                    - description: Селектор для описания
                    - link: Селектор для ссылки
                    - date: Селектор для даты
                - filter_keywords: Ключевые слова для фильтрации (опционально)
        """
        super().__init__(name, "webpage", config)
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        """
        Получение данных с веб-страницы
        
        Returns:
            Список записей с данными
        """
        url = self.config["url"]
        selectors = self.config.get("selectors", {})
        
        if not selectors or "item" not in selectors:
            logger.error(f"Не указаны селекторы для {self.name}")
            return []
        
        try:
            # Получаем содержимое веб-страницы
            response = self._make_request(url)
            
            # Парсим HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Находим все элементы с данными
            items = soup.select(selectors["item"])
            
            if not items:
                logger.warning(f"Не найдено элементов по селектору {selectors['item']} на странице {url}")
                return []
            
            # Фильтрация по ключевым словам, если указаны
            filter_keywords = self.config.get("filter_keywords", [])
            
            result = []
            for item in items:
                # Извлекаем данные по селекторам
                title_elem = item.select_one(selectors.get("title", ""))
                title = title_elem.text.strip() if title_elem else ""
                
                desc_elem = item.select_one(selectors.get("description", ""))
                description = desc_elem.text.strip() if desc_elem else ""
                
                link_elem = item.select_one(selectors.get("link", ""))
                link = link_elem["href"] if link_elem and link_elem.has_attr("href") else ""
                
                # Преобразуем относительные ссылки в абсолютные
                if link and not link.startswith(("http://", "https://")):
                    from urllib.parse import urljoin
                    link = urljoin(url, link)
                
                date_elem = item.select_one(selectors.get("date", ""))
                date_text = date_elem.text.strip() if date_elem else ""
                
                # Проверяем наличие ключевых слов в заголовке или описании
                if filter_keywords:
                    content = (title + " " + description).lower()
                    if not any(keyword.lower() in content for keyword in filter_keywords):
                        continue
                
                # Преобразуем дату в стандартный формат
                published = datetime.datetime.now().isoformat()
                if date_text:
                    try:
                        date_obj = self._parse_date(date_text)
                        published = date_obj.isoformat()
                    except Exception as e:
                        logger.warning(f"Ошибка при преобразовании даты: {e}")
                
                record = {
                    "source": self.name,
                    "source_type": self.source_type,
                    "id": self._generate_id({"title": title, "description": description}),
                    "title": title,
                    "description": description,
                    "published": published,
                    "link": link,
                    "raw_data": str(item)
                }
                
                result.append(record)
            
            self.last_update = datetime.datetime.now()
            return result
        
        except Exception as e:
            logger.error(f"Ошибка при получении данных с веб-страницы {self.name}: {e}")
            return []


class ThreatDataProcessor:
    """Класс для обработки и классификации данных об угрозах"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация процессора данных
        
        Args:
            config: Конфигурация процессора:
                - classifiers: Настройки классификаторов
                - extraction: Настройки извлечения данных
                - translation: Настройки перевода
        """
        self.config = config
        self.threat_categories = [
            "malware", "phishing", "ransomware", "ddos", "vulnerability", 
            "data_breach", "apt", "zero_day", "social_engineering", "mitm",
            "cryptojacking", "iot_threats", "insider_threat", "supply_chain"
        ]
        self.attack_vectors = [
            "email", "web", "network", "usb", "social", "wireless", 
            "cloud", "physical", "mobile", "api", "third_party"
        ]
        
        # Загружаем словари ключевых слов для категорий и векторов атак
        self.category_keywords = self._load_keywords("category_keywords.json")
        self.vector_keywords = self._load_keywords("vector_keywords.json")
    
    def _load_keywords(self, filename: str) -> Dict[str, List[str]]:
        """
        Загрузка ключевых слов из файла
        
        Args:
            filename: Имя файла со словарем ключевых слов
            
        Returns:
            Словарь ключевых слов по категориям
        """
        try:
            with open(os.path.join(os.path.dirname(__file__), "data", filename), 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Файл с ключевыми словами не найден: {filename}")
            # Возвращаем базовый словарь, если файл не найден
            if "category" in filename:
                return {
                    "malware": ["malware", "вирус", "троян", "червь", "backdoor"],
                    "phishing": ["фишинг", "phishing", "spoofing", "подделка"],
                    "ransomware": ["ransomware", "шифровальщик", "вымогатель"],
                    "vulnerability": ["уязвимость", "vulnerability", "exploit", "эксплойт"]
                }
            else:
                return {
                    "email": ["email", "почта", "спам", "письмо"],
                    "web": ["web", "веб", "сайт", "браузер", "http"],
                    "network": ["network", "сеть", "сетевой", "протокол"],
                    "usb": ["usb", "флэш", "накопитель", "removable"]
                }
    
    def process_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка отдельной записи данных
        
        Args:
            entry: Запись данных
            
        Returns:
            Обработанная запись с добавленными метаданными
        """
        # Создаем копию записи для обработки
        processed = entry.copy()
        
        # Объединяем заголовок и описание для анализа
        content = f"{entry['title']} {entry['description']}".lower()
        
        # Классификация категории угрозы
        processed["threat_categories"] = self._classify_by_keywords(content, self.category_keywords)
        
        # Классификация вектора атаки
        processed["attack_vectors"] = self._classify_by_keywords(content, self.vector_keywords)
        
        # Извлечение потенциальных индикаторов компрометации (IoC)
        processed["ioc"] = self._extract_ioc(content)
        
        # Оценка серьезности угрозы (от 1 до 10)
        processed["severity"] = self._evaluate_severity(processed)
        
        # Дополнительные метаданные
        processed["processed_date"] = datetime.datetime.now().isoformat()
        processed["version"] = "1.0"
        
        return processed
    
    def _classify_by_keywords(self, content: str, keyword_dict: Dict[str, List[str]]) -> List[str]:
        """
        Классификация текста по ключевым словам
        
        Args:
            content: Текст для классификации
            keyword_dict: Словарь ключевых слов по категориям
            
        Returns:
            Список обнаруженных категорий
        """
        result = []
        
        for category, keywords in keyword_dict.items():
            for keyword in keywords:
                if keyword.lower() in content:
                    if category not in result:
                        result.append(category)
                    break
        
        return result
    
    def _extract_ioc(self, content: str) -> Dict[str, List[str]]:
        """
        Извлечение индикаторов компрометации из текста
        
        Args:
            content: Текст для анализа
            
        Returns:
            Словарь с обнаруженными индикаторами по типам
        """
        # Инициализация словаря для результатов
        ioc = {
            "ip": [],
            "domain": [],
            "url": [],
            "email": [],
            "hash": [],
            "cve": []
        }
        
        # Регулярные выражения для различных типов IoC
        patterns = {
            "ip": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            "domain": r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b",
            "url": r"https?://(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}(?:/[a-zA-Z0-9\-._~:/?#[\]@!$&'()*+,;=]*)?",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "hash": r"\b[a-fA-F0-9]{32}\b|\b[a-fA-F0-9]{40}\b|\b[a-fA-F0-9]{64}\b",
            "cve": r"CVE-\d{4}-\d{4,}"
        }
        
        # Поиск по регулярным выражениям
        for ioc_type, pattern in patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            # Удаление дубликатов
            ioc[ioc_type] = list(set(matches))
        
        # Дополнительная фильтрация домена (исключение общих доменов)
        common_domains = ["example.com", "google.com", "microsoft.com", "apple.com", "facebook.com"]
        ioc["domain"] = [domain for domain in ioc["domain"] if domain.lower() not in common_domains]
        
        return ioc
    
    def _evaluate_severity(self, entry: Dict[str, Any]) -> int:
        """
        Оценка серьезности угрозы
        
        Args:
            entry: Обработанная запись
            
        Returns:
            Оценка серьезности (1-10)
        """
        score = 5  # Начальная оценка (средняя)
        
        # Факторы, повышающие оценку
        high_severity_categories = ["zero_day", "apt", "ransomware", "data_breach"]
        high_severity_words = ["critical", "критический", "urgent", "срочный", "zero-day", "нулевой день"]
        
        # Проверка категорий угроз
        for category in entry["threat_categories"]:
            if category in high_severity_categories:
                score += 1
        
        # Проверка ключевых слов в заголовке и описании
        content = f"{entry['title']} {entry['description']}".lower()
        for word in high_severity_words:
            if word in content:
                score += 1
                break
        
        # Проверка наличия IoC
        ioc_count = sum(len(iocs) for iocs in entry["ioc"].values())
        if ioc_count > 0:
            score += min(ioc_count // 2, 2)  # Максимум +2 за наличие IoC
        
        # Ограничение оценки диапазоном 1-10
        return max(1, min(score, 10))
    
    def process_entries(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Обработка списка записей
        
        Args:
            entries: Список записей для обработки
            
        Returns:
            Список обработанных записей
        """
        result = []
        
        # Многопоточная обработка записей
        with ThreadPoolExecutor(max_workers=min(10, len(entries))) as executor:
            result = list(executor.map(self.process_entry, entries))
        
        return result


class AutoEnrichmentModule:
    """Основной класс модуля автоматического обогащения базы знаний"""
    
    def __init__(self, config_path: str = None, kb_accessor: KnowledgeBaseAccessor = None):
        """
        Инициализация модуля автоматического обогащения
        
        Args:
            config_path: Путь к файлу конфигурации (по умолчанию ищется в текущей директории)
            kb_accessor: Экземпляр класса для работы с базой знаний (опционально)
        """
        # Загрузка конфигурации
        self.config = self._load_config(config_path)
        
        # Инициализация аксессора базы знаний
        self.kb_accessor = kb_accessor
        if self.kb_accessor is None:
            # Если не передан аксессор, создаем новый с параметрами из конфигурации
            kb_config = self.config.get("knowledge_base", {})
            self.kb_accessor = KnowledgeBaseAccessor(
                storage_type=kb_config.get("storage_type", "json"),
                path=kb_config.get("path", "./knowledge_base.json")
            )
        
        # Инициализация источников данных
        # Инициализация источников данных
        self.sources = self._init_sources()
        
        # Инициализация процессора данных
        self.processor = ThreatDataProcessor(self.config.get("processor", {}))
        
        # Инициализация хранилища для собранных данных
        self.storage = self._init_storage()
    
    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        """
        Загрузка конфигурации из файла
        
        Args:
            config_path: Путь к файлу конфигурации
            
        Returns:
            Словарь с конфигурацией
        """
        # Стандартный путь к конфигурации
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "config", "auto_enrichment_config.json")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info(f"Конфигурация загружена из {config_path}")
                return config
        except FileNotFoundError:
            logger.warning(f"Файл конфигурации не найден: {config_path}")
            logger.info("Используется конфигурация по умолчанию")
            return self._get_default_config()
        except json.JSONDecodeError:
            logger.error(f"Ошибка декодирования JSON в файле {config_path}")
            logger.info("Используется конфигурация по умолчанию")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Получение конфигурации по умолчанию
        
        Returns:
            Словарь с конфигурацией по умолчанию
        """
        return {
            "knowledge_base": {
                "storage_type": "json",
                "path": "./knowledge_base.json"
            },
            "sources": {
                "cve": {
                    "type": "api",
                    "url": "https://services.nvd.nist.gov/rest/json/cves/2.0",
                    "params": {
                        "resultsPerPage": 20
                    },
                    "response_format": "json",
                    "data_path": "vulnerabilities",
                    "title_field": "cve.id",
                    "description_field": "cve.descriptions[0].value",
                    "date_field": "cve.published",
                    "link_field": "cve.references[0].url"
                },
                "security_news": {
                    "type": "rss",
                    "url": "https://threatpost.ru/feed/",
                    "filter_keywords": ["vulnerability", "threat", "attack", "malware", "уязвимость", "атака", "угроза"]
                }
            },
            "storage": {
                "type": "sqlite",
                "path": "./auto_enrichment.db"
            },
            "processor": {
                "enable_translation": True,
                "translation_target_language": "ru"
            },
            "schedule": {
                "frequency": "daily",
                "time": "03:00"
            }
        }
    
    def _init_sources(self) -> Dict[str, ThreatIntelSource]:
        """
        Инициализация источников данных
        
        Returns:
            Словарь с экземплярами источников данных
        """
        sources = {}
        
        for name, config in self.config.get("sources", {}).items():
            source_type = config.get("type", "")
            
            if source_type == "api":
                sources[name] = APIThreatSource(name, config)
            elif source_type == "rss":
                sources[name] = RSSFeedSource(name, config)
            elif source_type == "webpage":
                sources[name] = WebPageSource(name, config)
            else:
                logger.warning(f"Неизвестный тип источника: {source_type} для {name}")
        
        logger.info(f"Инициализировано {len(sources)} источников данных")
        return sources
    
    def _init_storage(self) -> sqlite3.Connection:
        """
        Инициализация хранилища для собранных данных
        
        Returns:
            Объект соединения с базой данных
        """
        storage_config = self.config.get("storage", {})
        storage_type = storage_config.get("type", "sqlite")
        
        if storage_type == "sqlite":
            storage_path = storage_config.get("path", "./auto_enrichment.db")
            
            # Создаем директорию для хранилища, если её нет
            os.makedirs(os.path.dirname(os.path.abspath(storage_path)), exist_ok=True)
            
            # Подключаемся к базе данных SQLite
            connection = sqlite3.connect(storage_path)
            connection.row_factory = sqlite3.Row
            
            # Создаем таблицы, если их нет
            self._create_tables(connection)
            
            logger.info(f"Хранилище данных инициализировано: {storage_path}")
            return connection
        else:
            logger.error(f"Неподдерживаемый тип хранилища: {storage_type}")
            logger.info("Используется хранилище SQLite по умолчанию")
            
            # Используем SQLite по умолчанию
            storage_path = "./auto_enrichment.db"
            connection = sqlite3.connect(storage_path)
            connection.row_factory = sqlite3.Row
            
            # Создаем таблицы, если их нет
            self._create_tables(connection)
            
            return connection
    
    def _create_tables(self, connection: sqlite3.Connection) -> None:
        """
        Создание таблиц в хранилище
        
        Args:
            connection: Соединение с базой данных
        """
        cursor = connection.cursor()
        
        # Таблица для хранения информации об угрозах
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS threats (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            source_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            published TEXT,
            link TEXT,
            severity INTEGER,
            processed_date TEXT,
            version TEXT,
            added_to_kb BOOLEAN DEFAULT 0,
            raw_data TEXT
        )
        ''')
        
        # Таблица для категорий угроз
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS threat_categories (
            threat_id TEXT,
            category TEXT,
            PRIMARY KEY (threat_id, category),
            FOREIGN KEY (threat_id) REFERENCES threats(id) ON DELETE CASCADE
        )
        ''')
        
        # Таблица для векторов атак
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS attack_vectors (
            threat_id TEXT,
            vector TEXT,
            PRIMARY KEY (threat_id, vector),
            FOREIGN KEY (threat_id) REFERENCES threats(id) ON DELETE CASCADE
        )
        ''')
        
        # Таблицы для индикаторов компрометации (IoC)
        for ioc_type in ["ip", "domain", "url", "email", "hash", "cve"]:
            cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS ioc_{ioc_type} (
                threat_id TEXT,
                value TEXT,
                PRIMARY KEY (threat_id, value),
                FOREIGN KEY (threat_id) REFERENCES threats(id) ON DELETE CASCADE
            )
            ''')
        
        # Таблица для отслеживания запусков обновлений
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS enrichment_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT NOT NULL,
            end_time TEXT,
            status TEXT DEFAULT 'running',
            sources_count INTEGER,
            entries_fetched INTEGER DEFAULT 0,
            entries_processed INTEGER DEFAULT 0,
            entries_added_to_kb INTEGER DEFAULT 0,
            error_message TEXT
        )
        ''')
        
        connection.commit()
    
    def run_enrichment(self) -> Dict[str, Any]:
        """
        Выполнение процесса обогащения базы знаний
        
        Returns:
            Словарь с результатами процесса обогащения
        """
        logger.info("Запуск процесса обогащения базы знаний")
        
        # Создаем запись о запуске процесса
        run_id = self._create_run_record()
        
        try:
            # Сбор данных из всех источников
            all_entries = []
            for name, source in self.sources.items():
                logger.info(f"Получение данных из источника: {name}")
                entries = source.fetch_data()
                logger.info(f"Получено {len(entries)} записей из источника {name}")
                all_entries.extend(entries)
            
            # Обновляем запись о запуске
            self._update_run_record(run_id, {
                "entries_fetched": len(all_entries),
                "sources_count": len(self.sources)
            })
            
            # Если записей нет, завершаем процесс
            if not all_entries:
                logger.warning("Не получено новых данных ни из одного источника")
                self._update_run_record(run_id, {
                    "status": "completed",
                    "end_time": datetime.datetime.now().isoformat()
                })
                return {"status": "completed", "message": "Нет новых данных", "count": 0}
            
            # Обработка данных
            logger.info(f"Обработка {len(all_entries)} записей")
            processed_entries = self.processor.process_entries(all_entries)
            
            # Обновляем запись о запуске
            self._update_run_record(run_id, {
                "entries_processed": len(processed_entries)
            })
            
            # Сохранение обработанных данных
            added_count = self._save_processed_entries(processed_entries)
            
            # Интеграция в базу знаний
            added_to_kb_count = self._integrate_to_knowledge_base(processed_entries)
            
            # Обновляем запись о запуске
            self._update_run_record(run_id, {
                "entries_added_to_kb": added_to_kb_count,
                "status": "completed",
                "end_time": datetime.datetime.now().isoformat()
            })
            
            logger.info(f"Процесс обогащения завершен. Добавлено {added_count} записей")
            
            return {
                "status": "completed",
                "message": "Обогащение успешно выполнено",
                "count": added_count,
                "added_to_kb": added_to_kb_count
            }
        
        except Exception as e:
            logger.error(f"Ошибка при выполнении процесса обогащения: {e}")
            
            # Обновляем запись о запуске
            self._update_run_record(run_id, {
                "status": "error",
                "error_message": str(e),
                "end_time": datetime.datetime.now().isoformat()
            })
            
            return {"status": "error", "message": str(e)}
    
    def _create_run_record(self) -> int:
        """
        Создание записи о запуске процесса обогащения
        
        Returns:
            ID созданной записи
        """
        cursor = self.storage.cursor()
        cursor.execute('''
        INSERT INTO enrichment_runs (start_time, status)
        VALUES (?, ?)
        ''', (datetime.datetime.now().isoformat(), "running"))
        
        self.storage.commit()
        return cursor.lastrowid
    
    def _update_run_record(self, run_id: int, data: Dict[str, Any]) -> None:
        """
        Обновление записи о запуске процесса обогащения
        
        Args:
            run_id: ID записи
            data: Данные для обновления
        """
        cursor = self.storage.cursor()
        
        # Формируем запрос на обновление
        query = "UPDATE enrichment_runs SET "
        query_parts = []
        params = []
        
        for key, value in data.items():
            query_parts.append(f"{key} = ?")
            params.append(value)
        
        query += ", ".join(query_parts)
        query += " WHERE id = ?"
        params.append(run_id)
        
        cursor.execute(query, params)
        self.storage.commit()
    
    def _save_processed_entries(self, entries: List[Dict[str, Any]]) -> int:
        """
        Сохранение обработанных записей в хранилище
        
        Args:
            entries: Список обработанных записей
            
        Returns:
            Количество добавленных записей
        """
        cursor = self.storage.cursor()
        added_count = 0
        
        for entry in entries:
            # Проверяем наличие записи в базе
            cursor.execute("SELECT id FROM threats WHERE id = ?", (entry["id"],))
            existing = cursor.fetchone()
            
            if existing:
                # Если запись уже есть, обновляем её
                cursor.execute('''
                UPDATE threats SET
                    title = ?,
                    description = ?,
                    published = ?,
                    link = ?,
                    severity = ?,
                    processed_date = ?,
                    version = ?,
                    raw_data = ?
                WHERE id = ?
                ''', (
                    entry["title"],
                    entry["description"],
                    entry["published"],
                    entry["link"],
                    entry["severity"],
                    entry["processed_date"],
                    entry["version"],
                    json.dumps(entry["raw_data"]),
                    entry["id"]
                ))
                
                # Удаляем существующие категории, векторы атак и IoC
                cursor.execute("DELETE FROM threat_categories WHERE threat_id = ?", (entry["id"],))
                cursor.execute("DELETE FROM attack_vectors WHERE threat_id = ?", (entry["id"],))
                
                for ioc_type in ["ip", "domain", "url", "email", "hash", "cve"]:
                    cursor.execute(f"DELETE FROM ioc_{ioc_type} WHERE threat_id = ?", (entry["id"],))
            else:
                # Иначе добавляем новую запись
                cursor.execute('''
                INSERT INTO threats
                    (id, source, source_type, title, description, published, link, 
                     severity, processed_date, version, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    entry["id"],
                    entry["source"],
                    entry["source_type"],
                    entry["title"],
                    entry["description"],
                    entry["published"],
                    entry["link"],
                    entry["severity"],
                    entry["processed_date"],
                    entry["version"],
                    json.dumps(entry["raw_data"])
                ))
                added_count += 1
            
            # Добавляем категории угроз
            for category in entry["threat_categories"]:
                cursor.execute('''
                INSERT OR IGNORE INTO threat_categories (threat_id, category)
                VALUES (?, ?)
                ''', (entry["id"], category))
            
            # Добавляем векторы атак
            for vector in entry["attack_vectors"]:
                cursor.execute('''
                INSERT OR IGNORE INTO attack_vectors (threat_id, vector)
                VALUES (?, ?)
                ''', (entry["id"], vector))
            
            # Добавляем индикаторы компрометации (IoC)
            for ioc_type, values in entry["ioc"].items():
                for value in values:
                    cursor.execute(f'''
                    INSERT OR IGNORE INTO ioc_{ioc_type} (threat_id, value)
                    VALUES (?, ?)
                    ''', (entry["id"], value))
        
        self.storage.commit()
        return added_count
    
    def _integrate_to_knowledge_base(self, entries: List[Dict[str, Any]]) -> int:
        """
        Интеграция данных в базу знаний
        
        Args:
            entries: Список обработанных записей
            
        Returns:
            Количество записей, добавленных в базу знаний
        """
        added_count = 0
        
        # Обновляем или создаем раздел для угроз
        threats_section = self._get_or_create_threats_section()
        
        # Создаем подразделы для категорий угроз, если их нет
        category_subsections = {}
        for entry in entries:
            for category in entry["threat_categories"]:
                if category not in category_subsections:
                    subsection_id = f"threat_{category}"
                    # Преобразуем id в человекочитаемое название
                    category_name = category.replace("_", " ").title()
                    
                    # Получаем существующий подраздел или создаем новый
                    subsection = self._get_subsection(threats_section["id"], subsection_id)
                    if not subsection:
                        logger.info(f"Создание подраздела для категории угроз: {category_name}")
                        subsection = {
                            "id": subsection_id,
                            "name": category_name,
                            "content": {}
                        }
                        # Добавляем подраздел к разделу угроз
                        if self.kb_accessor.storage_type == "json":
                            if "subsections" not in threats_section:
                                threats_section["subsections"] = []
                            threats_section["subsections"].append(subsection)
                        else:
                            # Для SQLite используем метод библиотеки
                            pass  # Здесь нужно будет реализовать добавление подраздела для SQLite
                    
                    category_subsections[category] = subsection
        
        # Обновляем раздел угроз, если используется JSON
        if self.kb_accessor.storage_type == "json":
            for i, section in enumerate(self.kb_accessor.data.get("sections", [])):
                if section.get("id") == threats_section["id"]:
                    self.kb_accessor.data["sections"][i] = threats_section
                    break
        
        # Добавляем записи в соответствующие подразделы
        cursor = self.storage.cursor()
        
        for entry in entries:
            # Определяем категорию угрозы (берем первую, если их несколько)
            if not entry["threat_categories"]:
                continue
            
            primary_category = entry["threat_categories"][0]
            subsection = category_subsections.get(primary_category)
            
            if not subsection:
                continue
            
            # Генерируем идентификатор для записи в базе знаний
            threat_id = entry["id"]
            
            # Преобразуем запись в формат для базы знаний
            threat_data = {
                "term": entry["title"],
                "definition": entry["description"],
                "related_terms": entry["threat_categories"] + entry["attack_vectors"],
                "severity": entry["severity"],
                "date": entry["published"],
                "source": entry["source"],
                "link": entry["link"]
            }
            
            # Добавляем информацию об IoC, если они есть
            ioc_data = {}
            for ioc_type, values in entry["ioc"].items():
                if values:
                    ioc_data[ioc_type] = values
            
            if ioc_data:
                threat_data["indicators"] = ioc_data
            
            # Добавляем запись в базу знаний
            if self.kb_accessor.storage_type == "json":
                # Для JSON добавляем запись напрямую в подраздел
                if "content" not in subsection:
                    subsection["content"] = {}
                
                subsection["content"][threat_id] = threat_data
                added_count += 1
            else:
                # Для SQLite используем метод add_term
                try:
                    self.kb_accessor.add_term(
                        threat_data,
                        section_id=threats_section["id"],
                        subsection_id=subsection["id"]
                    )
                    added_count += 1
                except Exception as e:
                    logger.error(f"Ошибка при добавлении записи в базу знаний: {e}")
            
            # Отмечаем запись как добавленную в базу знаний
            cursor.execute('''
            UPDATE threats SET added_to_kb = 1
            WHERE id = ?
            ''', (entry["id"],))
        
        # Сохраняем изменения
        self.storage.commit()
        if self.kb_accessor.storage_type == "json":
            self.kb_accessor._save_json()
        
        return added_count
    
    def _get_or_create_threats_section(self) -> Dict[str, Any]:
        """
        Получение или создание раздела для угроз в базе знаний
        
        Returns:
            Словарь с информацией о разделе
        """
        section_id = "cyber_threats"
        
        # Получаем раздел, если он существует
        section = self.kb_accessor.get_section(section_id)
        
        if not section:
            # Создаем новый раздел для угроз
            logger.info("Создание раздела для угроз в базе знаний")
            section = {
                "id": section_id,
                "name": "Категории киберугроз",
                "description": "Классификация и описание основных типов киберугроз",
                "subsections": []
            }
            
            # Добавляем раздел в базу знаний
            self.kb_accessor.add_section(section)
            
            # Получаем обновленный раздел
            section = self.kb_accessor.get_section(section_id)
        
        return section
    
    def _get_subsection(self, section_id: str, subsection_id: str) -> Optional[Dict[str, Any]]:
        """
        Получение подраздела из базы знаний
        
        Args:
            section_id: ID раздела
            subsection_id: ID подраздела
            
        Returns:
            Словарь с информацией о подразделе или None, если подраздел не найден
        """
        if self.kb_accessor.storage_type == "json":
            section = self.kb_accessor.get_section(section_id)
            if section:
                for subsection in section.get("subsections", []):
                    if subsection.get("id") == subsection_id:
                        return subsection
            return None
        else:
            return self.kb_accessor.get_subsection(section_id, subsection_id)
    
    def get_latest_threats(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Получение последних обнаруженных угроз
        
        Args:
            limit: Максимальное количество записей
            
        Returns:
            Список записей об угрозах
        """
        cursor = self.storage.cursor()
        
        cursor.execute('''
        SELECT * FROM threats
        ORDER BY processed_date DESC
        LIMIT ?
        ''', (limit,))
        
        threats = []
        for row in cursor.fetchall():
            threat = dict(row)
            
            # Получаем категории угроз
            cursor.execute('''
            SELECT category FROM threat_categories
            WHERE threat_id = ?
            ''', (threat["id"],))
            threat["threat_categories"] = [row["category"] for row in cursor.fetchall()]
            
            # Получаем векторы атак
            cursor.execute('''
            SELECT vector FROM attack_vectors
            WHERE threat_id = ?
            ''', (threat["id"],))
            threat["attack_vectors"] = [row["vector"] for row in cursor.fetchall()]
            
            # Получаем индикаторы компрометации
            threat["ioc"] = {}
            for ioc_type in ["ip", "domain", "url", "email", "hash", "cve"]:
                cursor.execute(f'''
                SELECT value FROM ioc_{ioc_type}
                WHERE threat_id = ?
                ''', (threat["id"],))
                threat["ioc"][ioc_type] = [row["value"] for row in cursor.fetchall()]
            
            # Преобразуем raw_data обратно в объект
            if "raw_data" in threat and threat["raw_data"]:
                try:
                    threat["raw_data"] = json.loads(threat["raw_data"])
                except json.JSONDecodeError:
                    pass
            
            threats.append(threat)
        
        return threats
    
    def get_enrichment_stats(self) -> Dict[str, Any]:
        """
        Получение статистики процесса обогащения
        
        Returns:
            Словарь со статистикой
        """
        cursor = self.storage.cursor()
        
        # Общее количество записей
        cursor.execute("SELECT COUNT(*) as count FROM threats")
        total_count = cursor.fetchone()["count"]
        
        # Количество записей, добавленных в базу знаний
        cursor.execute("SELECT COUNT(*) as count FROM threats WHERE added_to_kb = 1")
        added_to_kb_count = cursor.fetchone()["count"]
        
        # Распределение по категориям
        cursor.execute('''
        SELECT category, COUNT(*) as count 
        FROM threat_categories
        GROUP BY category
        ORDER BY count DESC
        ''')
        categories = {}
        for row in cursor.fetchall():
            categories[row["category"]] = row["count"]
        
        # Распределение по векторам атак
        cursor.execute('''
        SELECT vector, COUNT(*) as count 
        FROM attack_vectors
        GROUP BY vector
        ORDER BY count DESC
        ''')
        vectors = {}
        for row in cursor.fetchall():
            vectors[row["vector"]] = row["count"]
        
        # Распределение по серьезности
        cursor.execute('''
        SELECT severity, COUNT(*) as count 
        FROM threats
        GROUP BY severity
        ORDER BY severity DESC
        ''')
        severity = {}
        for row in cursor.fetchall():
            severity[row["severity"]] = row["count"]
        
        # Распределение по источникам
        cursor.execute('''
        SELECT source, COUNT(*) as count 
        FROM threats
        GROUP BY source
        ORDER BY count DESC
        ''')
        sources = {}
        for row in cursor.fetchall():
            sources[row["source"]] = row["count"]
        
        # Последний запуск обогащения
        cursor.execute('''
        SELECT * FROM enrichment_runs
        ORDER BY start_time DESC
        LIMIT 1
        ''')
        last_run_row = cursor.fetchone()
        last_run = dict(last_run_row) if last_run_row else None
        
        return {
            "total_count": total_count,
            "added_to_kb_count": added_to_kb_count,
            "categories": categories,
            "vectors": vectors,
            "severity": severity,
            "sources": sources,
            "last_run": last_run
        }
    
    def schedule_enrichment(self) -> None:
        """
        Планирование регулярного обогащения базы знаний
        """
        # Этот метод будет реализован позже, когда появится возможность планирования задач
        pass
    
    def close(self) -> None:
        """
        Закрытие соединений с базами данных
        """
        if self.storage:
            self.storage.close()
        
        if self.kb_accessor:
            self.kb_accessor.close()
        
        logger.info("Соединения с базами данных закрыты")
