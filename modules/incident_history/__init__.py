#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль хронологии инцидентов кибербезопасности.
Предоставляет инструменты для сохранения, анализа и поиска информации об исторических инцидентах.
"""

from .incident_history_accessor import IncidentHistoryAccessor

__all__ = ['IncidentHistoryAccessor']
