#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Пример использования модуля интеграции с фреймворками MITRE ATT&CK и NIST
"""

import os
import sys
import json

# Добавляем путь к основной библиотеке
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from knowledge_base_accessor import KnowledgeBaseAccessor
from modules.mitre_nist import MitreNistAccessor

def print_separator():
    """Печать разделителя для наглядности вывода"""
    print("\n" + "=" * 80 + "\n")

def example_mitre_attack_integration():
    """Пример работы с интеграцией MITRE ATT&CK"""
    print("Пример работы с интеграцией MITRE ATT&CK")
    print_separator()
    
    # Создаем экземпляр основного класса для работы с базой знаний
    kb = KnowledgeBaseAccessor(storage_type="json", path="knowledge_base.json")
    
    # Создаем экземпляр класса для работы с MITRE ATT&CK и NIST
    mitre_nist = MitreNistAccessor(kb)
    
    # Добавляем тактику MITRE ATT&CK
    print("Добавление тактики MITRE ATT&CK...")
    try:
        tactic_id = mitre_nist.add_mitre_tactic({
            "id": "TA0001",
            "name": "Initial Access",
            "description": "Первоначальный доступ к целевой системе. Техники, которые используют различные векторы проникновения для получения начального доступа.",
            "url": "https://attack.mitre.org/tactics/TA0001/"
        })
        print(f"Добавлена тактика с ID: {tactic_id}")
    except ValueError as e:
        print(f"Ошибка при добавлении тактики: {e}")
    
    # Добавляем технику MITRE ATT&CK
    print("\nДобавление техники MITRE ATT&CK...")
    try:
        technique_id = mitre_nist.add_mitre_technique({
            "id": "T1566",
            "name": "Phishing",
            "description": "Фишинг - это попытка получить конфиденциальную информацию или данные от пользователя путем обмана.",
            "url": "https://attack.mitre.org/techniques/T1566/",
            "detection": "Анализ сетевого трафика, проверка вложений электронной почты, мониторинг поведения пользователей.",
            "mitigation": "Обучение пользователей, фильтрация электронной почты, защита от вредоносных программ.",
            "tactics": ["TA0001"]
        })
        print(f"Добавлена техника с ID: {technique_id}")
    except ValueError as e:
        print(f"Ошибка при добавлении техники: {e}")
    
    # Добавляем подтехнику MITRE ATT&CK
    print("\nДобавление подтехники MITRE ATT&CK...")
    try:
        subtechnique_id = mitre_nist.add_mitre_subtechnique({
            "id": "T1566.001",
            "parent_technique_id": "T1566",
            "name": "Spearphishing Attachment",
            "description": "Целевой фишинг с вложениями - это конкретный вариант фишинга, который использует вложения для доставки вредоносного кода.",
            "url": "https://attack.mitre.org/techniques/T1566/001/",
            "detection": "Сканирование вложений электронной почты, мониторинг выполнения процессов.",
            "mitigation": "Фильтрация вложений, обучение пользователей, изоляция приложений."
        })
        print(f"Добавлена подтехника с ID: {subtechnique_id}")
    except ValueError as e:
        print(f"Ошибка при добавлении подтехники: {e}")
    
    # Получаем список тактик
    print("\nСписок тактик MITRE ATT&CK:")
    tactics = mitre_nist.get_mitre_tactics()
    for tactic in tactics:
        print(f"- {tactic['id']}: {tactic['name']}")
    
    # Получаем список техник
    print("\nСписок техник MITRE ATT&CK (для тактики Initial Access):")
    techniques = mitre_nist.get_mitre_techniques(tactic_id="TA0001")
    for technique in techniques:
        print(f"- {technique['id']}: {technique['name']}")
        if "subtechniques" in technique and technique["subtechniques"]:
            for subtechnique in technique["subtechniques"]:
                print(f"  - {subtechnique['id']}: {subtechnique['name']}")
    
    # Связываем термин с техникой MITRE ATT&CK
    print("\nСвязывание термина с техникой MITRE ATT&CK...")
    
    # Сначала добавим новый термин, если его нет
    try:
        term_id = kb.add_term({
            "term": "Фишинг",
            "definition": "Вид интернет-мошенничества, целью которого является получение конфиденциальных данных пользователей.",
            "related_terms": ["социальная инженерия", "спам", "вредоносное ПО"]
        })
        print(f"Добавлен термин с ID: {term_id}")
    except Exception as e:
        print(f"Термин 'Фишинг' уже существует: {e}")
        # Найдем ID существующего термина
        term_id = "фишинг"
    
    # Связываем термин с техникой
    try:
        result = mitre_nist.link_term_to_mitre(term_id, "T1566", "technique")
        print(f"Связь термина с техникой успешно создана: {result}")
    except ValueError as e:
        print(f"Ошибка при связывании термина с техникой: {e}")
    
    # Связываем продукт с техникой MITRE ATT&CK
    print("\nСвязывание продукта с техникой MITRE ATT&CK...")
    try:
        result = mitre_nist.link_product_to_mitre(
            "intellectshield", 
            "T1566", 
            "technique",
            effectiveness="High",
            description="ИнтеллектЩит обнаруживает фишинговые атаки с помощью анализа поведения пользователей и сетевого трафика."
        )
        print(f"Связь продукта с техникой успешно создана: {result}")
    except ValueError as e:
        print(f"Ошибка при связывании продукта с техникой: {e}")
    
    # Закрываем соединение
    kb.close()
    
    print_separator()
    print("Пример работы с интеграцией MITRE ATT&CK завершен")

def example_nist_integration():
    """Пример работы с интеграцией NIST"""
    print("Пример работы с интеграцией NIST")
    print_separator()
    
    # Создаем экземпляр основного класса для работы с базой знаний
    kb = KnowledgeBaseAccessor(storage_type="json", path="knowledge_base.json")
    
    # Создаем экземпляр класса для работы с MITRE ATT&CK и NIST
    mitre_nist = MitreNistAccessor(kb)
    
    # Добавляем категорию NIST CSF
    print("Добавление категории NIST CSF...")
    try:
        category_id = mitre_nist.add_nist_category({
            "id": "ID",
            "name": "Identify",
            "framework": "CSF",
            "description": "Разработка организационного понимания для управления риском кибербезопасности в отношении систем, активов, данных и возможностей."
        })
        print(f"Добавлена категория с ID: {category_id}")
    except ValueError as e:
        print(f"Ошибка при добавлении категории: {e}")
    
    # Получаем список категорий NIST
    print("\nСписок категорий NIST CSF:")
    categories = mitre_nist.get_nist_categories(framework="CSF")
    for category in categories:
        print(f"- {category['id']}: {category['name']}")
    
    # Закрываем соединение
    kb.close()
    
    print_separator()
    print("Пример работы с интеграцией NIST завершен")

def main():
    """Основная функция для запуска примеров"""
    choice = None
    while choice != '0':
        print("\nПРИМЕРЫ ИСПОЛЬЗОВАНИЯ ИНТЕГРАЦИИ С MITRE ATT&CK И NIST")
        print("1. Пример работы с интеграцией MITRE ATT&CK")
        print("2. Пример работы с интеграцией NIST")
        print("0. Выход")
        
        choice = input("\nВыберите пример для запуска: ")
        
        if choice == '1':
            example_mitre_attack_integration()
        elif choice == '2':
            example_nist_integration()
        elif choice == '0':
            print("Выход из программы...")
        else:
            print("Неверный выбор. Пожалуйста, попробуйте снова.")

if __name__ == "__main__":
    main()
