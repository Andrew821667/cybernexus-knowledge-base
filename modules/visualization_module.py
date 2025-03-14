#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль визуализации связей между элементами базы знаний по кибербезопасности
Позволяет строить графы связей между терминами, угрозами и методами защиты
"""

import json
import os
import sqlite3
from typing import List, Dict, Any, Tuple, Optional
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Для работы без GUI


class KnowledgeGraphVisualizer:
    """Класс для визуализации связей в базе знаний"""
    
    def __init__(self, knowledge_base_path: str, storage_type: str = "json"):
        """
        Инициализация визуализатора
        
        Args:
            knowledge_base_path: Путь к файлу базы знаний
            storage_type: Тип хранилища ("json" или "sqlite")
        """
        self.knowledge_base_path = knowledge_base_path
        self.storage_type = storage_type.lower()
        self.graph = nx.DiGraph()
        
        # Параметры стилей для разных типов узлов
        self.node_styles = {
            "term": {"color": "skyblue", "shape": "o", "size": 1000},
            "product": {"color": "lightgreen", "shape": "s", "size": 1200},
            "threat": {"color": "salmon", "shape": "d", "size": 1000},
            "protection": {"color": "lightgray", "shape": "^", "size": 900}
        }
        
        self.edge_styles = {
            "related": {"color": "gray", "style": "--", "width": 1.0},
            "protects_from": {"color": "green", "style": "-", "width": 1.5},
            "threatens": {"color": "red", "style": "-", "width": 1.5},
            "includes": {"color": "blue", "style": "-", "width": 1.0}
        }
        
        # Загружаем данные
        self._load_data()
    
    def _load_data(self):
        """Загрузка данных из базы знаний"""
        if self.storage_type == "json":
            self._load_from_json()
        elif self.storage_type == "sqlite":
            self._load_from_sqlite()
        else:
            raise ValueError(f"Неподдерживаемый тип хранилища: {self.storage_type}")
    
    def _load_from_json(self):
        """Загрузка данных из JSON-файла"""
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Обработка терминов
            for section in data.get("sections", []):
                for subsection in section.get("subsections", []):
                    content = subsection.get("content", {})
                    
                    # Термины кибербезопасности
                    if "basic_terms" in subsection.get("id", ""):
                        for term_id, term_data in content.items():
                            # Добавляем узел термина
                            self.graph.add_node(
                                term_id,
                                label=term_data.get("term", term_id),
                                type="term",
                                definition=term_data.get("definition", "")
                            )
                            
                            # Добавляем связи между терминами
                            for related_term in term_data.get("related_terms", []):
                                related_id = related_term.lower().replace(" ", "_")
                                self.graph.add_edge(
                                    term_id,
                                    related_id,
                                    type="related"
                                )
                    
                    # Продукты
                    elif "products" in section.get("id", "") and content:
                        product_id = subsection.get("id", "")
                        self.graph.add_node(
                            product_id,
                            label=subsection.get("name", product_id),
                            type="product",
                            description=content.get("description", "")
                        )
            
            # Поиск существующих терминов, не определенных явно
            for node, edges in self.graph.adj.items():
                for target in edges:
                    if target not in self.graph:
                        self.graph.add_node(
                            target,
                            label=target.replace("_", " ").capitalize(),
                            type="term",
                            definition="(Определение отсутствует)"
                        )
            
            print(f"Загружено {self.graph.number_of_nodes()} узлов и {self.graph.number_of_edges()} связей из JSON")
        except Exception as e:
            print(f"Ошибка при загрузке данных из JSON: {e}")
    
    def _load_from_sqlite(self):
        """Загрузка данных из SQLite базы данных"""
        try:
            conn = sqlite3.connect(self.knowledge_base_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Загрузка терминов
            cursor.execute("""
                SELECT t.id, t.term, t.definition, t.subsection_id, rt.related_term
                FROM terms t
                LEFT JOIN related_terms rt ON t.id = rt.term_id
            """)
            
            terms = {}
            for row in cursor.fetchall():
                term_id = row["id"]
                if term_id not in terms:
                    terms[term_id] = {
                        "term": row["term"],
                        "definition": row["definition"],
                        "subsection_id": row["subsection_id"],
                        "related_terms": []
                    }
                
                if row["related_term"]:
                    terms[term_id]["related_terms"].append(row["related_term"])
            
            # Добавление терминов в граф
            for term_id, term_data in terms.items():
                node_id = term_data["term"].lower().replace(" ", "_")
                self.graph.add_node(
                    node_id,
                    label=term_data["term"],
                    type="term",
                    definition=term_data["definition"]
                )
                
                # Добавление связей
                for related_term in term_data["related_terms"]:
                    related_id = related_term.lower().replace(" ", "_")
                    self.graph.add_edge(
                        node_id,
                        related_id,
                        type="related"
                    )
            
            # Загрузка продуктов
            cursor.execute("""
                SELECT p.id, p.name, p.description
                FROM products p
            """)
            
            for row in cursor.fetchall():
                product_id = row["id"]
                self.graph.add_node(
                    product_id,
                    label=row["name"],
                    type="product",
                    description=row["description"]
                )
            
            # Поиск существующих терминов, не определенных явно
            for node, edges in self.graph.adj.items():
                for target in edges:
                    if target not in self.graph:
                        self.graph.add_node(
                            target,
                            label=target.replace("_", " ").capitalize(),
                            type="term",
                            definition="(Определение отсутствует)"
                        )
            
            conn.close()
            print(f"Загружено {self.graph.number_of_nodes()} узлов и {self.graph.number_of_edges()} связей из SQLite")
        except Exception as e:
            print(f"Ошибка при загрузке данных из SQLite: {e}")
    
    def add_relationship(self, source_id: str, target_id: str, relationship_type: str = "related"):
        """
        Добавление связи между элементами
        
        Args:
            source_id: ID исходного элемента
            target_id: ID целевого элемента
            relationship_type: Тип связи ("related", "protects_from", "threatens", "includes")
        """
        if relationship_type not in self.edge_styles:
            raise ValueError(f"Неподдерживаемый тип связи: {relationship_type}")
        
        # Проверяем существование узлов и добавляем если нужно
        if source_id not in self.graph:
            print(f"Узел {source_id} не найден, добавляем как неизвестный элемент")
            self.graph.add_node(
                source_id,
                label=source_id.replace("_", " ").capitalize(),
                type="term",
                definition="(Определение отсутствует)"
            )
        
        if target_id not in self.graph:
            print(f"Узел {target_id} не найден, добавляем как неизвестный элемент")
            self.graph.add_node(
                target_id,
                label=target_id.replace("_", " ").capitalize(),
                type="term",
                definition="(Определение отсутствует)"
            )
        
        # Добавляем связь
        self.graph.add_edge(
            source_id,
            target_id,
            type=relationship_type
        )
    
    def visualize(self, output_path: str = "knowledge_graph.png", graph_type: str = "spring",
                  highlight_nodes: List[str] = None, filter_by_type: List[str] = None, 
                  max_nodes: int = 50) -> str:
        """
        Визуализация графа знаний
        
        Args:
            output_path: Путь для сохранения изображения
            graph_type: Тип графа ("spring", "circular", "random", "hierarchical")
            highlight_nodes: Список ID узлов для выделения
            filter_by_type: Список типов узлов для фильтрации (term, product, threat, protection)
            max_nodes: Максимальное количество узлов для отображения
            
        Returns:
            Путь к сохраненному изображению
        """
        # Создаем подграф для визуализации
        if filter_by_type:
            nodes_to_include = [n for n, d in self.graph.nodes(data=True) if d.get("type") in filter_by_type]
            subgraph = self.graph.subgraph(nodes_to_include)
        else:
            subgraph = self.graph
        
        # Ограничиваем количество узлов, если граф слишком большой
        if subgraph.number_of_nodes() > max_nodes:
            print(f"Граф содержит {subgraph.number_of_nodes()} узлов, ограничиваем до {max_nodes}")
            # Стратегия: выбираем узлы с наибольшим количеством связей
            degree_sorted = sorted(subgraph.degree, key=lambda x: x[1], reverse=True)
            nodes_to_keep = [node for node, degree in degree_sorted[:max_nodes]]
            
            # Добавляем выделенные узлы, если они указаны
            if highlight_nodes:
                for node in highlight_nodes:
                    if node in subgraph and node not in nodes_to_keep:
                        nodes_to_keep.append(node)
            
            subgraph = subgraph.subgraph(nodes_to_keep)
        
        # Настройка отображения
        plt.figure(figsize=(16, 12))
        
        # Определяем расположение узлов
        if graph_type == "spring":
            pos = nx.spring_layout(subgraph, k=0.3, iterations=50)
        elif graph_type == "circular":
            pos = nx.circular_layout(subgraph)
        elif graph_type == "random":
            pos = nx.random_layout(subgraph)
        elif graph_type == "hierarchical":
            try:
                pos = graphviz_layout(subgraph, prog="dot")
            except:
                print("Ошибка при использовании graphviz, используем spring_layout")
                pos = nx.spring_layout(subgraph, k=0.3, iterations=50)
        else:
            pos = nx.spring_layout(subgraph, k=0.3, iterations=50)
        
        # Отрисовка рёбер разных типов
        edge_types = set(nx.get_edge_attributes(subgraph, 'type').values())
        for edge_type in edge_types:
            edges = [(u, v) for u, v, d in subgraph.edges(data=True) if d.get('type') == edge_type]
            style = self.edge_styles.get(edge_type, self.edge_styles["related"])
            nx.draw_networkx_edges(
                subgraph, pos,
                edgelist=edges,
                edge_color=style["color"],
                style=style["style"],
                width=style["width"],
                alpha=0.7
            )
        
        # Отрисовка узлов разных типов
        node_types = set(nx.get_node_attributes(subgraph, 'type').values())
        for node_type in node_types:
            nodes = [n for n, d in subgraph.nodes(data=True) if d.get('type') == node_type]
            style = self.node_styles.get(node_type, self.node_styles["term"])
            nx.draw_networkx_nodes(
                subgraph, pos,
                nodelist=nodes,
                node_color=style["color"],
                node_shape=style["shape"],
                node_size=style["size"],
                alpha=0.8
            )
        
        # Выделение узлов, если указаны
        if highlight_nodes:
            highlight_list = [n for n in highlight_nodes if n in subgraph]
            if highlight_list:
                nx.draw_networkx_nodes(
                    subgraph, pos,
                    nodelist=highlight_list,
                    node_color="yellow",
                    node_size=1500,
                    alpha=1.0
                )
        
        # Добавление меток
        labels = {n: d.get('label', n) for n, d in subgraph.nodes(data=True)}
        nx.draw_networkx_labels(
            subgraph, pos,
            labels=labels,
            font_size=10,
            font_weight='bold'
        )
        
        # Настройка отображения
        plt.title("Граф связей базы знаний по кибербезопасности", fontsize=16)
        plt.axis('off')
        
        # Добавляем легенду
        legend_elements = []
        for node_type, style in self.node_styles.items():
            if any(d.get('type') == node_type for _, d in subgraph.nodes(data=True)):
                legend_elements.append(plt.Line2D(
                    [0], [0],
                    marker=style["shape"],
                    color='w',
                    markerfacecolor=style["color"],
                    markersize=10,
                    label=node_type.capitalize()
                ))
        
        for edge_type, style in self.edge_styles.items():
            if any(d.get('type') == edge_type for _, _, d in subgraph.edges(data=True)):
                legend_elements.append(plt.Line2D(
                    [0], [0],
                    linestyle=style["style"],
                    color=style["color"],
                    linewidth=2,
                    label=edge_type.replace("_", " ").capitalize()
                ))
        
        plt.legend(handles=legend_elements, loc='best')
        
        # Сохраняем изображение
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        plt.savefig(output_path, bbox_inches='tight', dpi=150)
        plt.close()
        
        print(f"Граф сохранен в {output_path}")
        return output_path
    
    def export_graph(self, output_path: str = "knowledge_graph.graphml"):
        """
        Экспорт графа в формат GraphML для использования в специализированных программах
        
        Args:
            output_path: Путь для сохранения файла GraphML
            
        Returns:
            Путь к сохраненному файлу
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        nx.write_graphml(self.graph, output_path)
        print(f"Граф экспортирован в {output_path}")
        return output_path
    
    def get_relationships_for_node(self, node_id: str) -> Dict[str, List[str]]:
        """
        Получение всех связей для указанного узла
        
        Args:
            node_id: ID узла
            
        Returns:
            Словарь с исходящими и входящими связями
        """
        if node_id not in self.graph:
            print(f"Узел {node_id} не найден в графе")
            return {"outgoing": [], "incoming": []}
        
        outgoing = []
        for target, data in self.graph[node_id].items():
            target_data = self.graph.nodes[target]
            outgoing.append({
                "id": target,
                "label": target_data.get("label", target),
                "type": target_data.get("type", "unknown"),
                "relationship": data.get("type", "related")
            })
        
        incoming = []
        for source, targets in self.graph.pred[node_id].items():
            source_data = self.graph.nodes[source]
            for _, data in targets.items():
                incoming.append({
                    "id": source,
                    "label": source_data.get("label", source),
                    "type": source_data.get("type", "unknown"),
                    "relationship": data.get("type", "related")
                })
        
        return {
            "outgoing": outgoing,
            "incoming": incoming
        }
    
    def get_shortest_path(self, source_id: str, target_id: str) -> List[Tuple[str, str, str]]:
        """
        Поиск кратчайшего пути между двумя узлами
        
        Args:
            source_id: ID исходного узла
            target_id: ID целевого узла
            
        Returns:
            Список кортежей (node_id, node_label, node_type) с путём или пустой список
        """
        if source_id not in self.graph or target_id not in self.graph:
            print(f"Один из узлов не найден в графе")
            return []
        
        try:
            path = nx.shortest_path(self.graph, source=source_id, target=target_id)
            result = []
            for node_id in path:
                node_data = self.graph.nodes[node_id]
                result.append((
                    node_id,
                    node_data.get("label", node_id),
                    node_data.get("type", "unknown")
                ))
            return result
        except nx.NetworkXNoPath:
            print(f"Путь между {source_id} и {target_id} не найден")
            return []


# Пример использования
if __name__ == "__main__":
    # Создаем визуализатор для работы с JSON-файлом
    visualizer = KnowledgeGraphVisualizer("knowledge_base.json", "json")
    
    # Добавляем несколько новых связей для демонстрации
    visualizer.add_relationship("cybersecurity", "information_security", "related")
    visualizer.add_relationship("intellectshield", "cybersecurity", "protects_from")
    
    # Визуализируем граф
    os.makedirs("visualizations", exist_ok=True)
    graph_path = visualizer.visualize(
        output_path="visualizations/knowledge_graph.png",
        graph_type="spring",
        highlight_nodes=["cybersecurity"],
        max_nodes=30
    )
    
    # Экспортируем граф в формат GraphML
    visualizer.export_graph("visualizations/knowledge_graph.graphml")
    
    # Получаем все связи для узла "cybersecurity"
    relationships = visualizer.get_relationships_for_node("cybersecurity")
    print("Связи для узла 'cybersecurity':")
    print("Исходящие:", relationships["outgoing"])
    print("Входящие:", relationships["incoming"])
    
    # Ищем путь между двумя узлами
    path = visualizer.get_shortest_path("intellectshield", "information_security")
    if path:
        print("Кратчайший путь:")
        for node_id, node_label, node_type in path:
            print(f"  {node_label} ({node_type})")
