#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Расширение класса KnowledgeBaseAccessor для интеграции с MITRE ATT&CK и NIST
"""

from knowledge_base_accessor import KnowledgeBaseAccessor
from .mitre_nist_accessor import MitreNistAccessor

# Добавляем методы в основной класс KnowledgeBaseAccessor
def extend_knowledge_base_accessor():
    """
    Расширяет класс KnowledgeBaseAccessor методами для работы с MITRE ATT&CK и NIST
    """
    
    def init_mitre_nist(self):
        """Инициализация модуля MITRE ATT&CK и NIST"""
        self._mitre_nist = MitreNistAccessor(self)
        return self._mitre_nist
    
    # Добавляем метод в класс KnowledgeBaseAccessor
    setattr(KnowledgeBaseAccessor, 'init_mitre_nist', init_mitre_nist)
