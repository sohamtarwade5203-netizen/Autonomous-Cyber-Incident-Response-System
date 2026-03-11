# Ingestion package for Cyber Incident Response AI
from .elastic_connector import ElasticsearchConnector, get_elasticsearch_connector

__all__ = ['ElasticsearchConnector', 'get_elasticsearch_connector']
