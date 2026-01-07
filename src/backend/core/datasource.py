from abc import ABC, abstractmethod
from typing import List, Dict, Any

class DataSource(ABC):
    @abstractmethod
    def fetch_metrics(self, repo: str, metric_type: str) -> List[Dict[str, Any]]:
        """Fetch metrics for a given repository."""
        pass
    
    @abstractmethod
    def get_supported_metrics(self) -> List[str]:
        """Return list of supported metric keys."""
        pass

class OpenDiggerSource(DataSource):
    def fetch_metrics(self, repo: str, metric_type: str) -> List[Dict[str, Any]]:
        # This would eventually call the Opendigger API directly or via ETL script
        return []

    def get_supported_metrics(self) -> List[str]:
        return ["stars", "activity", "openrank", "bus_factor", "issues_new", "issues_closed"]
