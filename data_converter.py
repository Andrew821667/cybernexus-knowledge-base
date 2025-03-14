#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для преобразования базы знаний между форматами JSON и SQLite
"""

import json
import os
import argparse
import sqlite3
import shutil
import datetime

def json_to_sqlite(json_file, sqlite_file):
    """
    Преобразует базу знаний из формата JSON в SQLite
    
    Args:
        json_file: Путь к JSON-файлу
        sqlite_file: Путь к создаваемому SQLite-файлу
    """
    print(f"Преобразование JSON-файла '{json_file}' в SQLite-файл '{sqlite_file}'...")
    
    # Загружаем данные из JSON
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Ошибка: Файл '{json_file}' не найден.")
        return
    except json.JSONDecodeError:
        print(f"Ошибка: Файл '{json_file}' содержит некорректный JSON.")
        return
    
    # Удаляем существующую базу данных, если она есть
    if os.path.exists(sqlite_file):
        os.remove(sqlite_file)
    
    # Создаем схему базы данных
    schema_file = 'schema.sql'
    
    # Создаем соединение с базой данных
    conn = sqlite3.connect(sqlite_file)
    conn.row_factory = sqlite3.Row
    
    # Применяем схему
    try:
        with open(schema_file, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
    except FileNotFoundError:
        print(f"Ошибка: Файл схемы '{schema_file}' не найден.")
        conn.close()
        return
    
    # Начинаем транзакцию
    cursor = conn.cursor()
    
    try:
        # Информация о базе данных
        db_info = data.get("database_info", {})
        if db_info:
            cursor.execute(
                """
                INSERT INTO database_info (title, version, last_updated, description)
                VALUES (?, ?, ?, ?)
                """,
                (
                    db_info.get("title", "База знаний по кибербезопасности"),
                    db_info.get("version", "1.0"),
                    db_info.get("last_updated", ""),
                    db_info.get("description", "")
                )
            )
        
        # Информация о компании
        company_info = data.get("company", {})
        if company_info:
            cursor.execute(
                """
                INSERT INTO company (name, description, mission, unique_value, foundation_year)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    company_info.get("name", ""),
                    company_info.get("description", ""),
                    company_info.get("mission", ""),
                    company_info.get("unique_value", ""),
                    company_info.get("foundation_year")
                )
            )
        
        # Разделы и подразделы
        for i, section in enumerate(data.get("sections", [])):
            section_id = section.get("id", f"section_{i}")
            section_name = section.get("name", "")
            section_description = section.get("description", "")
            
            # Добавляем раздел
            cursor.execute(
                """
                INSERT INTO sections (id, name, description, order_index)
                VALUES (?, ?, ?, ?)
                """,
                (section_id, section_name, section_description, i)
            )
            
            # Добавляем подразделы
            for j, subsection in enumerate(section.get("subsections", [])):
                subsection_id = subsection.get("id", f"{section_id}_sub_{j}")
                subsection_name = subsection.get("name", "")
                
                cursor.execute(
                    """
                    INSERT INTO subsections (id, section_id, name, order_index)
                    VALUES (?, ?, ?, ?)
                    """,
                    (subsection_id, section_id, subsection_name, j)
                )
                
                # Обрабатываем содержимое подраздела
                content = subsection.get("content", {})
                
                # Обработка терминов
                if content and "basic_terms" in subsection_id:
                    for term_key, term_data in content.items():
                        # Добавляем термин
                        cursor.execute(
                            """
                            INSERT INTO terms (subsection_id, term, definition)
                            VALUES (?, ?, ?)
                            """,
                            (
                                subsection_id,
                                term_data.get("term", term_key),
                                term_data.get("definition", "")
                            )
                        )
                        
                        # Получаем ID добавленного термина
                        term_id = cursor.lastrowid
                        
                        # Добавляем связанные термины
                        for related_term in term_data.get("related_terms", []):
                            cursor.execute(
                                """
                                INSERT INTO related_terms (term_id, related_term)
                                VALUES (?, ?)
                                """,
                                (term_id, related_term)
                            )
                        
                        # Обновляем индекс поиска
                        cursor.execute(
                            """
                            INSERT INTO search_index 
                            (content, section, subsection, entity_type, entity_id)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                term_data.get("term", "") + " " + term_data.get("definition", ""),
                                section_id,
                                subsection_id,
                                "term",
                                term_id
                            )
                        )
                
                # Обработка моделей безопасности
                elif content and "security_models" in subsection_id:
                    for model_key, model_data in content.items():
                        # Добавляем модель
                        cursor.execute(
                            """
                            INSERT INTO security_models (subsection_id, name, description)
                            VALUES (?, ?, ?)
                            """,
                            (
                                subsection_id,
                                model_data.get("name", model_key),
                                model_data.get("description", "")
                            )
                        )
                        
                        # Получаем ID добавленной модели
                        model_id = cursor.lastrowid
                        
                        # Добавляем компоненты модели
                        for component in model_data.get("components", []):
                            cursor.execute(
                                """
                                INSERT INTO model_components (model_id, name, description)
                                VALUES (?, ?, ?)
                                """,
                                (
                                    model_id,
                                    component.get("name", ""),
                                    component.get("description", "")
                                )
                            )
                            
                            # Получаем ID добавленного компонента
                            component_id = cursor.lastrowid
                            
                            # Добавляем меры защиты для компонента
                            for measure in component.get("measures", []):
                                cursor.execute(
                                    """
                                    INSERT INTO component_measures (component_id, measure)
                                    VALUES (?, ?)
                                    """,
                                    (component_id, measure)
                                )
                
                # Обработка продуктов
                elif "products" in section_id and not content:
                    # Добавляем продукт
                    cursor.execute(
                        """
                        INSERT INTO products (id, name, description, subsection_id)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            subsection_id,
                            subsection.get("name", ""),
                            subsection.get("description", ""),
                            subsection_id
                        )
                    )
                    
                    # Добавляем целевую аудиторию
                    product_content = content if content else subsection.get("content", {})
                    for audience in product_content.get("target_audience", []):
                        cursor.execute(
                            """
                            INSERT INTO product_audience (product_id, audience)
                            VALUES (?, ?)
                            """,
                            (subsection_id, audience)
                        )
                    
                    # Добавляем ключевые особенности
                    for feature in product_content.get("key_features", []):
                        cursor.execute(
                            """
                            INSERT INTO product_features (product_id, feature)
                            VALUES (?, ?)
                            """,
                            (subsection_id, feature)
                        )
                    
                    # Добавляем технические характеристики
                    tech_data = product_content.get("technology", {})
                    if tech_data:
                        cursor.execute(
                            """
                            INSERT INTO product_technology 
                            (product_id, core, architecture, visualization)
                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                subsection_id,
                                tech_data.get("core", ""),
                                tech_data.get("architecture", ""),
                                tech_data.get("visualization", "")
                            )
                        )
                        
                        # Получаем ID добавленной технологии
                        tech_id = cursor.lastrowid
                        
                        # Добавляем источники данных
                        for source in tech_data.get("data_sources", []):
                            cursor.execute(
                                """
                                INSERT INTO product_data_sources (technology_id, data_source)
                                VALUES (?, ?)
                                """,
                                (tech_id, source)
                            )
                    
                    # Добавляем кейсы
                    for case in product_content.get("case_studies", []):
                        cursor.execute(
                            """
                            INSERT INTO case_studies 
                            (product_id, customer, challenge, solution, results)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                subsection_id,
                                case.get("customer", ""),
                                case.get("challenge", ""),
                                case.get("solution", ""),
                                case.get("results", "")
                            )
                        )
        
        # Завершаем транзакцию
        conn.commit()
        print(f"Преобразование завершено. Создана SQLite база данных: {sqlite_file}")
    
    except Exception as e:
        # Откатываем изменения в случае ошибки
        conn.rollback()
        print(f"Ошибка при преобразовании данных: {e}")
    finally:
        # Закрываем соединение
        conn.close()

def sqlite_to_json(sqlite_file, json_file):
    """
    Преобразует базу знаний из формата SQLite в JSON
    
    Args:
        sqlite_file: Путь к SQLite-файлу
        json_file: Путь к создаваемому JSON-файлу
    """
    print(f"Преобразование SQLite-файла '{sqlite_file}' в JSON-файл '{json_file}'...")
    
    # Проверяем существование базы данных
    if not os.path.exists(sqlite_file):
        print(f"Ошибка: Файл '{sqlite_file}' не найден.")
        return
    
    # Подключаемся к базе данных
    try:
        conn = sqlite3.connect(sqlite_file)
        conn.row_factory = sqlite3.Row
    except sqlite3.Error as e:
        print(f"Ошибка при подключении к базе данных: {e}")
        return
    
    # Создаем структуру JSON
    export_data = {
        "database_info": {},
        "company": {},
        "sections": []
    }
    
    cursor = conn.cursor()
    
    try:
        # Получаем информацию о базе данных
        cursor.execute("SELECT * FROM database_info LIMIT 1")
        db_info = cursor.fetchone()
        if db_info:
            export_data["database_info"] = dict(db_info)
        
        # Получаем информацию о компании
        cursor.execute("SELECT * FROM company LIMIT 1")
        company_info = cursor.fetchone()
        if company_info:
            export_data["company"] = dict(company_info)
        
        # Получаем все разделы
        cursor.execute("SELECT * FROM sections ORDER BY order_index")
        sections = [dict(row) for row in cursor.fetchall()]
        
        for section in sections:
            section_id = section["id"]
            
            # Получаем подразделы для каждого раздела
            cursor.execute("SELECT * FROM subsections WHERE section_id = ? ORDER BY order_index", (section_id,))
            subsections = [dict(row) for row in cursor.fetchall()]
            
            section["subsections"] = []
            
            for subsection in subsections:
                subsection_id = subsection["id"]
                
                # В зависимости от типа подраздела, получаем соответствующий контент
                if "basic_terms" in subsection_id:
                    # Получаем термины
                    cursor.execute("SELECT * FROM terms WHERE subsection_id = ?", (subsection_id,))
                    terms = [dict(row) for row in cursor.fetchall()]
                    
                    subsection["content"] = {}
                    
                    for term in terms:
                        term_id = term["id"]
                        term_name = term["term"].lower().replace(" ", "_")
                        
                        # Получаем связанные термины
                        cursor.execute("SELECT related_term FROM related_terms WHERE term_id = ?", (term_id,))
                        related_terms = [row["related_term"] for row in cursor.fetchall()]
                        
                        subsection["content"][term_name] = {
                            "term": term["term"],
                            "definition": term["definition"],
                            "related_terms": related_terms
                        }
                
                # Если это продукт
                elif "products" in section_id:
                    # Получаем информацию о продукте
                    cursor.execute("SELECT * FROM products WHERE id = ?", (subsection_id,))
                    product = cursor.fetchone()
                    
                    if product:
                        if "content" not in subsection:
                            subsection["content"] = {}
                        
                        subsection["content"]["description"] = product["description"]
                        
                        # Получаем целевую аудиторию
                        cursor.execute("SELECT audience FROM product_audience WHERE product_id = ?", (subsection_id,))
                        subsection["content"]["target_audience"] = [row["audience"] for row in cursor.fetchall()]
                        
                        # Получаем особенности
                        cursor.execute("SELECT feature FROM product_features WHERE product_id = ?", (subsection_id,))
                        subsection["content"]["key_features"] = [row["feature"] for row in cursor.fetchall()]
                        
                        # Получаем технические характеристики
                        cursor.execute("SELECT * FROM product_technology WHERE product_id = ?", (subsection_id,))
                        tech = cursor.fetchone()
                        
                        if tech:
                            subsection["content"]["technology"] = {
                                "core": tech["core"],
                                "architecture": tech["architecture"],
                                "visualization": tech["visualization"]
                            }
                            
                            # Получаем источники данных
                            cursor.execute("SELECT data_source FROM product_data_sources WHERE technology_id = ?", (tech["id"],))
                            subsection["content"]["technology"]["data_sources"] = [row["data_source"] for row in cursor.fetchall()]
                        
                        # Получаем кейсы
                        cursor.execute("SELECT * FROM case_studies WHERE product_id = ?", (subsection_id,))
                        subsection["content"]["case_studies"] = [dict(row) for row in cursor.fetchall()]
                
                section["subsections"].append(subsection)
            
            export_data["sections"].append(section)
        
        # Сохраняем данные в JSON
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"Преобразование завершено. Создан JSON-файл: {json_file}")
    
    except Exception as e:
        print(f"Ошибка при преобразовании данных: {e}")
    finally:
        conn.close()

def create_backup(file_path):
    """
    Создает резервную копию файла
    
    Args:
        file_path: Путь к файлу
        
    Returns:
        Путь к резервной копии или None, если файл не существует
    """
    if not os.path.exists(file_path):
        return None
    
    # Создаем директорию для резервных копий
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Создаем имя для резервной копии
    filename = os.path.basename(file_path)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"{os.path.splitext(filename)[0]}_{timestamp}{os.path.splitext(filename)[1]}")
    
    # Копируем файл
    shutil.copy2(file_path, backup_path)
    
    return backup_path

def main():
    """Основная функция скрипта"""
    parser = argparse.ArgumentParser(description="Преобразование базы знаний между форматами JSON и SQLite")
    
    # Аргументы командной строки
    parser.add_argument("--to-sqlite", action="store_true", help="Преобразовать из JSON в SQLite")
    parser.add_argument("--to-json", action="store_true", help="Преобразовать из SQLite в JSON")
    parser.add_argument("--input", "-i", required=True, help="Путь к входному файлу")
    parser.add_argument("--output", "-o", required=True, help="Путь к выходному файлу")
    parser.add_argument("--backup", "-b", action="store_true", help="Создать резервную копию входного файла")
    
    args = parser.parse_args()
    
    # Проверка аргументов
    if args.to_sqlite and args.to_json:
        print("Ошибка: Невозможно одновременно использовать --to-sqlite и --to-json")
        return
    
    if not (args.to_sqlite or args.to_json):
        print("Ошибка: Необходимо указать направление преобразования (--to-sqlite или --to-json)")
        return
    
    # Проверка существования входного файла
    if not os.path.exists(args.input):
        print(f"Ошибка: Входной файл '{args.input}' не найден.")
        return
    
    # Создание резервной копии
    if args.backup:
        backup_path = create_backup(args.input)
        if backup_path:
            print(f"Создана резервная копия: {backup_path}")
    
    # Выполнение преобразования
    if args.to_sqlite:
        json_to_sqlite(args.input, args.output)
    else:
        sqlite_to_json(args.input, args.output)

if __name__ == "__main__":
    main()
