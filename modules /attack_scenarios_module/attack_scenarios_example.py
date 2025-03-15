#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Примеры использования модуля сценариев атак
"""

from knowledge_base_accessor import KnowledgeBaseAccessor
import json
import os


def print_separator():
    """Печать разделителя для наглядности вывода"""
    print("\n" + "=" * 80 + "\n")


def example_attack_scenarios_json():
    """Пример работы с модулем сценариев атак в формате JSON"""
    print("Пример работы с модулем сценариев атак в формате JSON")
    print_separator()
    
    # Создаем экземпляр для работы с JSON
    kb = KnowledgeBaseAccessor(storage_type="json", path="knowledge_base.json")
    
    # Добавляем новый сценарий атаки
    print("Добавление нового сценария атаки...")
    
    scenario_data = {
        "id": "web_application_attack",
        "name": "Атака на веб-приложение с использованием SQL-инъекции",
        "description": "Сценарий атаки на веб-приложение с использованием уязвимости SQL-инъекции для получения доступа к базе данных и кражи конфиденциальной информации",
        "difficulty_level": "Medium",
        "impact_level": "High",
        "typical_duration": "1-3 дня",
        "detection_complexity": "Medium",
        "mitigation_complexity": "Low",
        "tags": ["sql injection", "web application", "data breach", "CVE-2021-1234"],
        "mitre_attack_ids": ["TA0001", "TA0002", "TA0009"],
        "threat_actors": ["Киберпреступники", "Хакактивисты"],
        "stages": [
            {
                "stage_id": "reconnaissance",
                "name": "Разведка",
                "description": "Сбор информации о целевом веб-приложении",
                "order_index": 1,
                "techniques": [
                    {
                        "name": "Сканирование портов",
                        "description": "Использование инструментов сканирования для выявления открытых портов и сервисов",
                        "mitre_technique_id": "T1046"
                    },
                    {
                        "name": "Поиск уязвимых форм",
                        "description": "Выявление форм ввода, потенциально уязвимых к SQL-инъекции",
                        "mitre_technique_id": "T1595"
                    }
                ]
            },
            {
                "stage_id": "exploitation",
                "name": "Эксплуатация",
                "description": "Использование уязвимости SQL-инъекции для получения доступа к базе данных",
                "order_index": 2,
                "techniques": [
                    {
                        "name": "SQL-инъекция",
                        "description": "Внедрение вредоносного SQL-кода в параметры запроса",
                        "mitre_technique_id": "T1190"
                    }
                ]
            },
            {
                "stage_id": "exfiltration",
                "name": "Эксфильтрация данных",
                "description": "Извлечение конфиденциальных данных из базы данных",
                "order_index": 3,
                "techniques": [
                    {
                        "name": "Извлечение данных по HTTP",
                        "description": "Использование HTTP-запросов для извлечения данных из базы данных",
                        "mitre_technique_id": "T1048.003"
                    }
                ]
            }
        ],
        "target_assets": [
            {
                "asset_type": "Веб-сервер",
                "asset_description": "Сервер с веб-приложением"
            },
            {
                "asset_type": "База данных",
                "asset_description": "База данных, содержащая конфиденциальную информацию о пользователях"
            }
        ],
        "mitigations": [
            {
                "name": "Параметризованные запросы",
                "description": "Использование параметризованных запросов вместо конкатенации строк SQL",
                "effectiveness": "High",
                "implementation_complexity": "Low",
                "stage_id": "exploitation"
            },
            {
                "name": "Web Application Firewall",
                "description": "Настройка WAF для блокировки запросов, содержащих признаки SQL-инъекции",
                "effectiveness": "Medium",
                "implementation_complexity": "Medium",
                "stage_id": "exploitation"
            },
            {
                "name": "ИнтеллектЩит",
                "description": "Использование ИнтеллектЩит для обнаружения аномального поведения и предотвращения эксфильтрации данных",
                "effectiveness": "High",
                "implementation_complexity": "Medium",
                "stage_id": "exfiltration",
                "product_id": "intellectshield"
            }
        ],
        "iocs": [
            {
                "ioc_type": "URL",
                "ioc_value": "/login.php?id=1' OR '1'='1",
                "description": "Пример URL с SQL-инъекцией"
            },
            {
                "ioc_type": "Network",
                "ioc_value": "Множественные запросы к /login.php с различными параметрами",
                "description": "Признак перебора параметров для поиска уязвимости"
            }
        ],
        "real_world_examples": [
            {
                "incident_name": "Атака на Equifax",
                "incident_date": "2017-05-13",
                "affected_organizations": "Equifax",
                "description": "Одна из крупнейших утечек данных, затронувшая более 147 миллионов человек",
                "outcome": "Украдены личные данные, номера социального страхования и кредитных карт",
                "lessons_learned": "Необходимость своевременной установки обновлений безопасности и проактивного мониторинга",
                "references": "https://www.ftc.gov/enforcement/cases-proceedings/refunds/equifax-data-breach-settlement"
            }
        ]
    }
    
    kb.add_attack_scenario(scenario_data, "web_attacks")
    
    # Получаем список всех сценариев атак
    print("\nСписок всех сценариев атак:")
    scenarios = kb.get_attack_scenarios()
    for scenario in scenarios:
        print(f"- {scenario['name']} ({scenario['id']})")
        print(f"  Уровень сложности: {scenario['difficulty_level']}")
        print(f"  Уровень воздействия: {scenario['impact_level']}")
        print(f"  Теги: {scenario.get('tags', '')}")
        print(f"  Этапы атаки ({len(scenario.get('stages', []))}): {', '.join([stage['name'] for stage in scenario.get('stages', [])])}")
    
    # Получаем конкретный сценарий атаки
    print("\nПолучение информации о сценарии 'web_application_attack':")
    scenario = kb.get_attack_scenario_by_id("web_application_attack")
    if scenario:
        print(f"Название: {scenario['name']}")
        print(f"Описание: {scenario['description']}")
        print("Этапы атаки:")
        for stage in scenario.get('stages', []):
            print(f"  {stage['order_index']}. {stage['name']}: {stage['description']}")
            print("    Техники:")
            for technique in stage.get('techniques', []):
                print(f"      - {technique['name']}: {technique['description']}")
        
        print("Меры защиты:")
        for mitigation in scenario.get('mitigations', []):
            print(f"  - {mitigation['name']}: {mitigation['description']}")
            if mitigation.get('product_id'):
                print(f"    Используемый продукт: {mitigation['product_id']}")
    else:
        print("Сценарий не найден")
    
    # Поиск сценариев по тегу
    print("\nПоиск сценариев по тегу 'sql injection':")
    tagged_scenarios = kb.get_attack_scenarios_by_tag("sql injection")
    for scenario in tagged_scenarios:
        print(f"- {scenario['name']}")
    
    # Поиск сценариев по продукту
    print("\nСценарии, использующие продукт 'intellectshield' для защиты:")
    product_scenarios = kb.get_attack_scenarios_by_product("intellectshield")
    for scenario in product_scenarios:
        print(f"- {scenario['name']}")
    
    # Поиск сценариев по технике MITRE ATT&CK
    print("\nСценарии, использующие технику 'T1190' (Exploit Public-Facing Application):")
    technique_scenarios = kb.get_attack_scenarios_by_mitre_technique("T1190")
    for scenario in technique_scenarios:
        print(f"- {scenario['name']}")
    
    # Удаляем сценарий
    print("\nУдаление сценария 'web_application_attack':")
    if kb.delete_attack_scenario("web_application_attack"):
        print("Сценарий успешно удален")
    else:
        print("Ошибка при удалении сценария")
    
    # Проверяем, что сценарий удален
    print("\nПроверка, что сценарий удален:")
    if kb.get_attack_scenario_by_id("web_application_attack"):
        print("Сценарий все еще существует")
    else:
        print("Сценарий успешно удален")
    
    # Закрываем соединение
    kb.close()
    
    print_separator()
    print("Пример работы с модулем сценариев атак в JSON-формате завершен")


def example_attack_scenarios_sqlite():
    """Пример работы с модулем сценариев атак в формате SQLite"""
    print("Пример работы с модулем сценариев атак в формате SQLite")
    print_separator()
    
    # Проверяем наличие файла базы данных
    if not os.path.exists("knowledge_base.db"):
        print("База данных SQLite не найдена. Создайте её с помощью data_converter.py")
        return
    
    # Создаем экземпляр для работы с SQLite
    kb = KnowledgeBaseAccessor(storage_type="sqlite", path="knowledge_base.db")
    
    # Здесь повторите примеры аналогично JSON-формату
    # ...
    
    # Закрываем соединение
    kb.close()
    
    print_separator()
    print("Пример работы с модулем сценариев атак в SQLite-формате завершен")


def main():
    """Основная функция для запуска примеров"""
    # Проверка и создание директорий
    os.makedirs('exports', exist_ok=True)
    os.makedirs('backups', exist_ok=True)
    
    choice = None
    while choice != '0':
        print("\nПРИМЕРЫ ИСПОЛЬЗОВАНИЯ МОДУЛЯ СЦЕНАРИЕВ АТАК")
        print("1. Пример работы с модулем сценариев атак в формате JSON")
        print("2. Пример работы с модулем сценариев атак в формате SQLite")
        print("0. Выход")
        
        choice = input("\nВыберите пример для запуска: ")
        
        if choice == '1':
            example_attack_scenarios_json()
        elif choice == '2':
            example_attack_scenarios_sqlite()
        elif choice == '0':
            print("Выход из программы...")
        else:
            print("Неверный выбор. Пожалуйста, попробуйте снова.")


if __name__ == "__main__":
    main()
