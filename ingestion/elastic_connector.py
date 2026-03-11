"""
Elasticsearch Connector for Cyber Incident Response AI

Provides enterprise-grade log storage, indexing, and search capabilities.
Fully offline operation - connects to local Elasticsearch instance only.
"""

from elasticsearch import Elasticsearch, helpers
from typing import List, Dict, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ElasticsearchConnector:
    """
    Manages Elasticsearch connections and operations for security alerts and incidents.
    """
    
    def __init__(self, hosts: List[str] = None, index_prefix: str = "cyber-ir"):
        """
        Initialize Elasticsearch connector.
        
        Args:
            hosts: List of Elasticsearch hosts (default: localhost:9200)
            index_prefix: Prefix for all indices (default: cyber-ir)
        """
        self.hosts = hosts or ["http://localhost:9200"]
        self.index_prefix = index_prefix
        self.es = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Elasticsearch with retry logic."""
        try:
            self.es = Elasticsearch(
                self.hosts,
                request_timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
            
            # Verify connection
            if self.es.ping():
                logger.info(f"Connected to Elasticsearch at {self.hosts}")
                self._create_index_templates()
            else:
                logger.error("Failed to ping Elasticsearch")
                self.es = None
        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {str(e)}")
            self.es = None
    
    def _create_index_templates(self):
        """Create index templates for alerts and incidents."""
        
        # Alert index template
        alert_template = {
            "index_patterns": [f"{self.index_prefix}-alerts-*"],
            "template": {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "refresh_interval": "5s"
                },
                "mappings": {
                    "properties": {
                        "timestamp": {"type": "date"},
                        "source": {"type": "keyword"},
                        "attack_type": {"type": "keyword"},
                        "severity": {"type": "keyword"},
                        "src_ip": {"type": "ip"},
                        "dst_ip": {"type": "ip"},
                        "src_port": {"type": "integer"},
                        "dst_port": {"type": "integer"},
                        "protocol": {"type": "keyword"},
                        "is_anomaly": {"type": "boolean"},
                        "anomaly_score": {"type": "float"},
                        "burst_score": {"type": "float"}
                    }
                }
            }
        }
        
        # Incident index template
        incident_template = {
            "index_patterns": [f"{self.index_prefix}-incidents-*"],
            "template": {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0
                },
                "mappings": {
                    "properties": {
                        "incident_id": {"type": "keyword"},
                        "attack_type": {"type": "keyword"},
                        "alert_count": {"type": "integer"},
                        "anomaly_confidence": {"type": "float"},
                        "behavior_risk": {"type": "keyword"},
                        "priority": {"type": "keyword"},
                        "fidelity_score": {"type": "float"},
                        "created_at": {"type": "date"},
                        "status": {"type": "keyword"},
                        "playbook": {"type": "text"}
                    }
                }
            }
        }
        
        try:
            # Create templates (ES 8.x uses _index_template)
            self.es.indices.put_index_template(
                name=f"{self.index_prefix}-alerts-template",
                body=alert_template
            )
            self.es.indices.put_index_template(
                name=f"{self.index_prefix}-incidents-template",
                body=incident_template
            )
            logger.info("Created Elasticsearch index templates")
        except Exception as e:
            logger.error(f"Failed to create index templates: {str(e)}")
    
    def bulk_index_alerts(self, alerts: List[Dict], index_suffix: str = None) -> bool:
        """
        Bulk index alerts into Elasticsearch.
        
        Args:
            alerts: List of alert dictionaries
            index_suffix: Optional index suffix (default: current date)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.es:
            logger.warning("Elasticsearch not connected, skipping indexing")
            return False
        
        if not alerts:
            logger.warning("No alerts to index")
            return False
        
        # Generate index name with date suffix
        if not index_suffix:
            index_suffix = datetime.now().strftime("%Y.%m.%d")
        index_name = f"{self.index_prefix}-alerts-{index_suffix}"
        
        # Prepare bulk actions
        actions = []
        for alert in alerts:
            action = {
                "_index": index_name,
                "_source": alert
            }
            actions.append(action)
        
        try:
            # Bulk index
            success, failed = helpers.bulk(
                self.es,
                actions,
                chunk_size=1000,
                raise_on_error=False
            )
            
            logger.info(f"Indexed {success} alerts to {index_name}, {len(failed)} failed")
            return len(failed) == 0
            
        except Exception as e:
            logger.error(f"Bulk indexing failed: {str(e)}")
            return False
    
    def index_incident(self, incident: Dict, index_suffix: str = None) -> bool:
        """
        Index a single incident.
        
        Args:
            incident: Incident dictionary
            index_suffix: Optional index suffix (default: current date)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.es:
            logger.warning("Elasticsearch not connected, skipping indexing")
            return False
        
        if not index_suffix:
            index_suffix = datetime.now().strftime("%Y.%m")
        index_name = f"{self.index_prefix}-incidents-{index_suffix}"
        
        try:
            result = self.es.index(
                index=index_name,
                document=incident
            )
            logger.info(f"Indexed incident {incident.get('incident_id')} to {index_name}")
            return result['result'] in ['created', 'updated']
        except Exception as e:
            logger.error(f"Failed to index incident: {str(e)}")
            return False
    
    def search_alerts(self, query: Dict, size: int = 100) -> List[Dict]:
        """
        Search alerts using Elasticsearch query DSL.
        
        Args:
            query: Elasticsearch query dictionary
            size: Maximum number of results
        
        Returns:
            List of matching alerts
        """
        if not self.es:
            logger.warning("Elasticsearch not connected")
            return []
        
        try:
            result = self.es.search(
                index=f"{self.index_prefix}-alerts-*",
                body=query,
                size=size
            )
            
            hits = result['hits']['hits']
            return [hit['_source'] for hit in hits]
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []
    
    def get_alert_stats(self) -> Dict:
        """
        Get aggregated statistics on alerts.
        
        Returns:
            Dictionary with alert statistics
        """
        if not self.es:
            return {}
        
        query = {
            "size": 0,
            "aggs": {
                "by_attack_type": {
                    "terms": {"field": "attack_type", "size": 10}
                },
                "by_severity": {
                    "terms": {"field": "severity", "size": 10}
                },
                "anomaly_count": {
                    "filter": {"term": {"is_anomaly": True}}
                },
                "total_count": {
                    "value_count": {"field": "_id"}
                }
            }
        }
        
        try:
            result = self.es.search(
                index=f"{self.index_prefix}-alerts-*",
                body=query
            )
            
            aggs = result['aggregations']
            return {
                "total_alerts": aggs['total_count']['value'],
                "anomalous_alerts": aggs['anomaly_count']['doc_count'],
                "by_attack_type": {
                    bucket['key']: bucket['doc_count']
                    for bucket in aggs['by_attack_type']['buckets']
                },
                "by_severity": {
                    bucket['key']: bucket['doc_count']
                    for bucket in aggs['by_severity']['buckets']
                }
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {str(e)}")
            return {}
    
    def health_check(self) -> Dict:
        """
        Check Elasticsearch cluster health.
        
        Returns:
            Dictionary with health status
        """
        if not self.es:
            return {"status": "disconnected"}
        
        try:
            health = self.es.cluster.health()
            return {
                "status": health['status'],
                "cluster_name": health['cluster_name'],
                "number_of_nodes": health['number_of_nodes'],
                "active_shards": health['active_shards']
            }
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {"status": "error", "message": str(e)}


# Singleton instance
_es_connector = None

def get_elasticsearch_connector(hosts: List[str] = None) -> ElasticsearchConnector:
    """Get or create Elasticsearch connector singleton."""
    global _es_connector
    if _es_connector is None:
        _es_connector = ElasticsearchConnector(hosts=hosts)
    return _es_connector
