#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Пример использования модуля хронологии инцидентов кибербезопасности
"""

import os
import sys
import json
from datetime import datetime, timedelta
import random

# Добавляем родительскую директорию в путь для импорта основной библиотеки
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge_base_accessor import KnowledgeBaseAccessor
from incident_history.incident_history_accessor import IncidentHistoryAccessor

def print_separator():
    """Печать разделителя для наглядности вывода"""
    print("
" + "=" * 80 + "
")

def demo_json_storage():
    """Демонстрация работы с хронологией инцидентов в формате JSON"""
    print("Демонстрация работы с хронологией инцидентов в формате JSON")
    print_separator()
    
    # Создаем экземпляр для работы с базой знаний
    kb = KnowledgeBaseAccessor(storage_type="json", path="knowledge_base.json")
    
    # Создаем экземпляр для работы с хронологией инцидентов
    ih = IncidentHistoryAccessor(storage_type="json", kb_accessor=kb)
    
    # Получаем список категорий инцидентов
    print("Список категорий инцидентов:")
    categories = ih.get_categories()
    for category in categories:
        print(f"- {category['name']}: {category['description']}")
    
    # Добавляем новую категорию
    print("
Добавление новой категории инцидентов:")
    category_id = ih.add_category(
        name="Ransomware Attack",
        description="Атаки с использованием программ-вымогателей, шифрующих данные и требующих выкуп"
    )
    print(f"Добавлена категория с ID: {category_id}")
    
    # Добавляем новый инцидент
    print("
Добавление нового инцидента:")
    incident_data = {
        "title": "Атака программы-вымогателя на медицинскую организацию",
        "description": "Крупная медицинская организация подверглась атаке программы-вымогателя, которая зашифровала критические данные пациентов и системы управления.",
        "date_occurred": datetime.now().strftime("%Y-%m-%d"),
        "date_discovered": datetime.now().strftime("%Y-%m-%d"),
        "date_resolved": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
        "severity": "Critical",
        "category_id": category_id,
        "affected_systems": "Системы электронных медицинских карт, системы планирования, серверы резервного копирования",
        "impact_description": "Временная недоступность медицинских данных, отмена плановых процедур, перенаправление экстренных пациентов",
        "estimated_financial_impact": 1500000,
        "organizations_affected": 1,
        "source_url": "https://example.com/incident-report",
        "tags": ["ransomware", "healthcare", "patient-data", "critical-infrastructure"],
        "techniques": [
            {
                "technique_id": "T1566",
                "description": "Фишинговое письмо с вредоносным вложением"
            },
            {
                "technique_id": "T1486",
                "description": "Шифрование данных для воздействия"
            }
        ],
        "phases": [
            {
                "phase_name": "Initial Access",
                "description": "Доступ получен через фишинговое письмо, отправленное сотруднику отдела кадров"
            },
            {
                "phase_name": "Execution",
                "description": "Запуск вредоносного макроса в документе Word"
            },
            {
                "phase_name": "Privilege Escalation",
                "description": "Использование уязвимости для повышения привилегий"
            },
            {
                "phase_name": "Lateral Movement",
                "description": "Распространение по сети с использованием украденных учетных данных"
            },
            {
                "phase_name": "Impact",
                "description": "Шифрование критических данных и систем"
            }
        ],
        "lessons_learned": [
            {
                "lesson": "Недостаточная осведомленность персонала о фишинговых атаках",
                "recommendation": "Усилить программу обучения персонала по кибербезопасности",
                "priority": "High",
                "corrective_actions": [
                    {
                        "action": "Разработать и внедрить ежемесячные тренинги по фишингу",
                        "status": "In Progress"
                    },
                    {
                        "action": "Внедрить симуляции фишинговых атак для проверки бдительности",
                        "status": "Planned"
                    }
                ]
            },
            {
                "lesson": "Неполное резервное копирование критических систем",
                "recommendation": "Внедрить изолированное и полное резервное копирование данных",
                "priority": "High",
                "corrective_actions": [
                    {
                        "action": "Внедрить офлайн-резервирование критических данных по схеме 3-2-1",
                        "status": "Planned"
                    }
                ]
            }
        ],
        "regions": [
            {
                "region": "United States",
                "is_source": False
            },
            {
                "region": "Eastern Europe",
                "is_source": True
            }
        ]
    }
    
    incident_id = ih.add_incident(incident_data)
    print(f"Добавлен инцидент с ID: {incident_id}")
    
    # Получаем информацию о добавленном инциденте
    print("
Информация о добавленном инциденте:")
    incident = ih.get_incident(incident_id)
    print(f"Название: {incident['title']}")
    print(f"Критичность: {incident['severity']}")
    print(f"Дата: {incident['date_occurred']}")
    print(f"Затронутые системы: {incident['affected_systems']}")
    print("Фазы атаки:")
    for phase in incident.get('phases', []):
        print(f"  - {phase['phase_name']}: {phase['description']}")
    
    # Поиск инцидентов
    print("
Поиск инцидентов по тегу 'ransomware':")
    search_results = ih.search_incidents(tags=["ransomware"])
    for result in search_results:
        print(f"- {result['title']} ({result['date_occurred']})")
    
    # Статистика по инцидентам
    print("
Статистика по инцидентам:")
    stats = ih.get_statistics()
    print(f"Общее количество инцидентов: {stats['total_incidents']}")
    print("Инциденты по категориям:")
    for category, count in stats.get('categories', {}).items():
        print(f"  - {category}: {count}")
    
    # Закрываем соединение
    ih.close()
    kb.close()
    
    print_separator()
    print("Демонстрация работы с JSON-хранилищем завершена")

def demo_sqlite_storage():
    """Демонстрация работы с хронологией инцидентов в формате SQLite"""
    print("Демонстрация работы с хронологией инцидентов в формате SQLite")
    print_separator()
    
    # Удаляем существующий файл базы данных для чистой демонстрации
    if os.path.exists("incident_history.db"):
        os.remove("incident_history.db")
    
    # Создаем экземпляр для работы с базой знаний
    kb = KnowledgeBaseAccessor(storage_type="sqlite", path="knowledge_base.db")
    
    # Создаем экземпляр для работы с хронологией инцидентов
    ih = IncidentHistoryAccessor(storage_type="sqlite", path="incident_history.db")
    
    # Проверяем наличие предустановленных категорий
    print("Предустановленные категории инцидентов:")
    categories = ih.get_categories()
    for category in categories:
        print(f"- {category['name']}")
    
    # Добавляем примеры инцидентов
    print("
Добавление примеров инцидентов:")
    
    # Список названий компаний
    companies = ["XYZ Corp", "ABC Healthcare", "MegaRetail", "TechInnovations", "FinanceFirst", "GovAgency"]
    
    # Список возможных систем
    systems = [
        "Active Directory", "Exchange Server", "Web Application", "Database Server", 
        "Customer Portal", "Mobile Application", "Cloud Infrastructure", "Internal Network"
    ]
    
    # Список возможных техник MITRE ATT&CK
    mitre_techniques = [
        {"id": "T1566", "name": "Phishing"},
        {"id": "T1078", "name": "Valid Accounts"},
        {"id": "T1190", "name": "Exploit Public-Facing Application"},
        {"id": "T1486", "name": "Data Encrypted for Impact"},
        {"id": "T1048", "name": "Exfiltration Over Alternative Protocol"},
        {"id": "T1027", "name": "Obfuscated Files or Information"}
    ]
    
    # Список возможных фаз атаки
    attack_phases = [
        "Initial Access", "Execution", "Persistence", "Privilege Escalation", 
        "Defense Evasion", "Credential Access", "Discovery", "Lateral Movement", 
        "Collection", "Command and Control", "Exfiltration", "Impact"
    ]
    
    # Список возможных тегов
    possible_tags = [
        "ransomware", "data-breach", "ddos", "phishing", "vulnerability", 
        "insider", "supply-chain", "apt", "malware", "zero-day", "credential-theft"
    ]
    
    # Список уроков
    possible_lessons = [
        "Недостаточная сегментация сети",
        "Слабая конфигурация брандмауэра",
        "Отсутствие многофакторной аутентификации",
        "Неактуальные патчи безопасности",
        "Недостаточное обучение персонала",
        "Слабые пароли в критических системах",
        "Чрезмерные привилегии пользователей",
        "Отсутствие мониторинга безопасности",
        "Недостаточное резервное копирование",
        "Отсутствие плана реагирования на инциденты"
    ]
    
    # Список рекомендаций
    possible_recommendations = [
        "Внедрить сегментацию сети",
        "Усилить конфигурацию брандмауэра",
        "Внедрить многофакторную аутентификацию",
        "Установить регулярное обновление патчей",
        "Усилить программу обучения по безопасности",
        "Внедрить политику сложных паролей",
        "Внедрить принцип наименьших привилегий",
        "Улучшить мониторинг безопасности",
        "Внедрить надежное резервное копирование",
        "Разработать план реагирования на инциденты"
    ]
    
    # Список регионов
    regions = [
        "North America", "South America", "Western Europe", "Eastern Europe", 
        "Middle East", "Africa", "East Asia", "Southeast Asia", "Australia"
    ]
    
    # Генерируем и добавляем 5 случайных инцидентов
    severities = ["Critical", "High", "Medium", "Low"]
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*2)  # За последние 2 года
    
    for i in range(5):
        # Случайная дата в пределах 2 лет
        incident_date = start_date + timedelta(days=random.randint(0, 730))
        discovery_date = incident_date + timedelta(days=random.randint(0, 7))
        resolution_date = discovery_date + timedelta(days=random.randint(1, 30))
        
        # Выбираем случайную категорию
        category = random.choice(categories)
        
        # Генерируем случайную технику MITRE ATT&CK
        techniques = random.sample(mitre_techniques, k=random.randint(1, 3))
        attack_techniques = []
        for technique in techniques:
            attack_techniques.append({
                "technique_id": technique["id"],
                "description": f"Использование {technique['name']}"
            })
        
        # Выбираем случайные фазы атаки
        selected_phases = random.sample(attack_phases, k=random.randint(3, 6))
        selected_phases.sort(key=lambda x: attack_phases.index(x))
        phases = []
        for j, phase in enumerate(selected_phases):
            phases.append({
                "phase_name": phase,
                "description": f"Описание фазы {phase}",
                "order_index": j
            })
        
        # Генерируем случайные теги
        tags = random.sample(possible_tags, k=random.randint(2, 5))
        
        # Генерируем случайные извлеченные уроки
        selected_lessons = random.sample(possible_lessons, k=random.randint(1, 3))
        lessons_learned = []
        for lesson in selected_lessons:
            # Выбираем случайную рекомендацию
            recommendation = random.choice(possible_recommendations)
            
            lessons_learned.append({
                "lesson": lesson,
                "recommendation": recommendation,
                "priority": random.choice(["High", "Medium", "Low"]),
                "corrective_actions": [
                    {
                        "action": f"Действие 1 для '{lesson}'",
                        "status": random.choice(["Planned", "In Progress", "Completed"])
                    },
                    {
                        "action": f"Действие 2 для '{lesson}'",
                        "status": random.choice(["Planned", "In Progress", "Completed"])
                    }
                ]
            })
        
        # Выбираем регионы
        target_region = random.choice(regions)
        source_region = random.choice([r for r in regions if r != target_region])
        incident_regions = [
            {"region": target_region, "is_source": False},
            {"region": source_region, "is_source": True}
        ]
        
        # Создаем инцидент
        incident_data = {
            "title": f"Инцидент {i+1}: {category['name']} в {random.choice(companies)}",
            "description": f"Описание инцидента {i+1} с категорией {category['name']}.",
            "date_occurred": incident_date.strftime("%Y-%m-%d"),
            "date_discovered": discovery_date.strftime("%Y-%m-%d"),
            "date_resolved": resolution_date.strftime("%Y-%m-%d"),
            "severity": random.choice(severities),
            "category_id": category["id"],
            "affected_systems": ", ".join(random.sample(systems, k=random.randint(1, 3))),
            "impact_description": f"Описание воздействия инцидента {i+1}",
            "estimated_financial_impact": random.randint(10000, 2000000),
            "organizations_affected": random.randint(1, 5),
            "source_url": f"https://example.com/incident-{i+1}",
            "tags": tags,
            "techniques": attack_techniques,
            "phases": phases,
            "lessons_learned": lessons_learned,
            "regions": incident_regions
        }
        
        incident_id = ih.add_incident(incident_data)
        print(f"Добавлен инцидент {i+1} с ID: {incident_id}")
    
    # Выполняем поиск инцидентов
    print("
Поиск инцидентов по тексту 'инцидент':")
    search_results = ih.search_incidents("инцидент")
    for result in search_results:
        print(f"- {result['title']} ({result['date_occurred']})")
    
    # Фильтрация по критичности
    print("
Фильтрация инцидентов с критичностью 'High':")
    filter_results = ih.search_incidents(severity="High")
    for result in filter_results:
        print(f"- {result['title']} ({result['severity']})")
    
    # Получаем статистику
    print("
Статистика по инцидентам:")
    stats = ih.get_statistics()
    print(f"Общее количество инцидентов: {stats['total_incidents']}")
    
    print("Инциденты по категориям:")
    for category, count in stats.get('categories', {}).items():
        print(f"  - {category}: {count}")
    
    print("Инциденты по уровням критичности:")
    for severity, count in stats.get('severities', {}).items():
        print(f"  - {severity}: {count}")
    
    # Закрываем соединение
    ih.close()
    kb.close()
    
    print_separator()
    print("Демонстрация работы с SQLite-хранилищем завершена")

def main():
    """Основная функция для запуска примеров"""
    print("ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ МОДУЛЯ ХРОНОЛОГИИ ИНЦИДЕНТОВ")
    print_separator()
    
    choice = None
    while choice != '0':
        print("
Выберите пример для запуска:")
        print("1. Работа с хронологией инцидентов в формате JSON")
        print("2. Работа с хронологией инцидентов в формате SQLite")
        print("0. Выход")
        
        choice = input("
Ваш выбор: ")
        
        if choice == '1':
            demo_json_storage()
        elif choice == '2':
            demo_sqlite_storage()
        elif choice == '0':
            print("Выход из программы...")
        else:
            print("Неверный выбор. Пожалуйста, попробуйте снова.")

if __name__ == "__main__":
    main()
