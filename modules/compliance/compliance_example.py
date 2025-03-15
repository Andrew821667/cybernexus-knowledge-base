#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Пример использования модуля соответствия нормативным требованиям
"""

from modules.compliance.compliance_accessor import ComplianceAccessor
import json
import os


def print_separator():
    """Печать разделителя для наглядности вывода"""
    print("\n" + "=" * 80 + "\n")


def example_json_storage():
    """Пример работы с данными о соответствии в формате JSON"""
    print("Пример работы с данными о соответствии в формате JSON")
    print_separator()
    
    # Создаем экземпляр для работы с JSON
    comp = ComplianceAccessor(storage_type="json", path="compliance_data.json")
    
    # Добавляем новый нормативный документ
    print("Добавление нового нормативного документа...")
    gdpr_id = comp.add_compliance_document({
        "code": "GDPR",
        "name": "General Data Protection Regulation",
        "description": "Регламент Европейского союза о защите персональных данных",
        "issuer": "European Parliament and Council",
        "issue_date": "2016-04-14",
        "effective_date": "2018-05-25",
        "scope": "Персональные данные граждан ЕС",
        "region": "European Union",
        "url": "https://gdpr-info.eu/",
        "document_type": "regulation"
    })
    print(f"Добавлен документ с ID: {gdpr_id}")
    
    # Добавляем еще один нормативный документ
    print("\nДобавление российского закона о персональных данных...")
    fz152_id = comp.add_compliance_document({
        "code": "152-ФЗ",
        "name": "О персональных данных",
        "description": "Федеральный закон Российской Федерации о персональных данных",
        "issuer": "Государственная Дума РФ",
        "issue_date": "2006-07-27",
        "effective_date": "2007-07-27",
        "scope": "Персональные данные граждан РФ",
        "region": "Российская Федерация",
        "url": "http://www.consultant.ru/document/cons_doc_LAW_61801/",
        "document_type": "law"
    })
    print(f"Добавлен документ с ID: {fz152_id}")
    
    # Добавляем требование для GDPR
    print("\nДобавление требования для GDPR...")
    requirement_id = comp.add_compliance_requirement({
        "document_id": gdpr_id,
        "code": "Art. 5(1)(a)",
        "name": "Принципы обработки персональных данных: законность, справедливость и прозрачность",
        "description": "Персональные данные должны обрабатываться законно, справедливо и прозрачным образом по отношению к субъекту данных.",
        "priority": "Высокий"
    })
    print(f"Добавлено требование с ID: {requirement_id}")
    
    # Добавляем контрольную меру
    print("\nДобавление контрольной меры...")
    control_id = comp.add_compliance_control({
        "name": "Политика конфиденциальности",
        "description": "Разработка и публикация политики конфиденциальности для пользователей",
        "implementation_status": "Внедрено",
        "responsible_role": "Руководитель службы безопасности",
        "verification_method": "Аудит документации"
    })
    print(f"Добавлена контрольная мера с ID: {control_id}")
    
    # Связываем требование с контрольной мерой
    print("\nСвязывание требования с контрольной мерой...")
    comp.link_requirement_to_control(requirement_id, control_id)
    print("Требование связано с контрольной мерой")
    
    # Добавляем несоответствие
    print("\nДобавление несоответствия...")
    gap_id = comp.add_compliance_gap({
        "requirement_id": requirement_id,
        "description": "Отсутствие механизма подтверждения согласия пользователя на обработку персональных данных",
        "impact": "Риск претензий со стороны надзорных органов и субъектов данных",
        "risk_level": "Высокий",
        "remediation_plan": "Внедрить механизм подтверждения согласия через вебформы и мобильное приложение",
        "due_date": "2025-06-30",
        "status": "В работе",
        "responsible_person": "Иванов И.И."
    })
    print(f"Добавлено несоответствие с ID: {gap_id}")
    
    # Получаем информацию о добавленных документах
    print("\nСписок нормативных документов:")
    documents = comp.get_compliance_documents()
    for document in documents:
        print(f"- {document['code']}: {document['name']} ({document['document_type']})")
    
    # Получаем требования по документу
    print("\nТребования для GDPR:")
    requirements = comp.get_compliance_requirements(gdpr_id)
    for req in requirements:
        print(f"- {req['code']}: {req['name']}")
        print(f"  Описание: {req['description']}")
        print(f"  Приоритет: {req['priority']}")
    
    # Получаем контрольные меры для требования
    print("\nКонтрольные меры для требования:")
    controls = comp.get_controls_for_requirement(requirement_id)
    for control in controls:
        print(f"- {control['name']}")
        print(f"  Описание: {control['description']}")
        print(f"  Статус: {control['implementation_status']}")
    
    # Получаем несоответствия для требования
    print("\nНесоответствия по требованию:")
    gaps = comp.get_compliance_gaps(requirement_id)
    for gap in gaps:
        print(f"- {gap['description']}")
        print(f"  Уровень риска: {gap['risk_level']}")
        print(f"  Статус: {gap['status']}")
        print(f"  Срок устранения: {gap['due_date']}")
    
    # Закрываем соединение
    comp.close()
    
    print_separator()
    print("Пример работы с JSON-хранилищем завершен")


def example_sqlite_storage():
    """Пример работы с данными о соответствии в формате SQLite"""
    print("Пример работы с данными о соответствии в формате SQLite")
    print_separator()
    
    # Создаем экземпляр для работы с SQLite
    comp = ComplianceAccessor(storage_type="sqlite", path="compliance_data.db")
    
    # Добавляем контрольную меру
    print("Добавление контрольной меры...")
    control_id = comp.add_compliance_control({
        "name": "Процедура управления инцидентами безопасности",
        "description": "Формализованный процесс обнаружения, регистрации и реагирования на инциденты безопасности",
        "implementation_status": "В процессе",
        "responsible_role": "Руководитель службы ИБ",
        "verification_method": "Аудит процедур и тестирование"
    })
    print(f"Добавлена контрольная мера с ID: {control_id}")
    
    # Смотрим список нормативных документов в SQLite
    print("\nСписок нормативных документов в SQLite:")
    documents = comp.get_compliance_documents()
    for document in documents:
        print(f"- {document['code']}: {document['name']} ({document.get('document_type', 'Не указан')})")
    
    # Смотрим список контрольных мер
    print("\nСписок контрольных мер:")
    controls = comp.get_compliance_controls()
    for control in controls:
        print(f"- {control['name']}")
        print(f"  Статус: {control['implementation_status']}")
        print(f"  Ответственный: {control['responsible_role']}")
    
    # Закрываем соединение
    comp.close()
    
    print_separator()
    print("Пример работы с SQLite-хранилищем завершен")


def main():
    """Основная функция для запуска примеров"""
    choice = None
    while choice != '0':
        print("\nПРИМЕРЫ ИСПОЛЬЗОВАНИЯ МОДУЛЯ СООТВЕТСТВИЯ НОРМАТИВНЫМ ТРЕБОВАНИЯМ")
        print("1. Пример работы с данными в формате JSON")
        print("2. Пример работы с данными в формате SQLite")
        print("0. Выход")
        
        choice = input("\nВыберите пример для запуска: ")
        
        if choice == '1':
            example_json_storage()
        elif choice == '2':
            example_sqlite_storage()
        elif choice == '0':
            print("Выход из программы...")
        else:
            print("Неверный выбор. Пожалуйста, попробуйте снова.")


if __name__ == "__main__":
    main()
