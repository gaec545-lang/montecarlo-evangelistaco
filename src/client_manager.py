import yaml
from typing import List, Dict, Optional
from datetime import date
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Client:
    """Representa un cliente (empresa) del SaaS"""
    client_id: str
    name: str
    industry: str
    status: str  # active, inactive, suspended
    created_at: str
    config_file: str
    supabase_url: Optional[str] = None  # NO se guarda en YAML, solo en boveda
    supabase_key: Optional[str] = None  # NO se guarda en YAML, solo en boveda


class ClientManager:
    """Gestiona el registro de clientes del SaaS"""

    def __init__(self, registry_file: str = "configs/clients_registry.yaml"):
        self.registry_file = registry_file
        self._ensure_file_exists()
        self.data = self._load()

    def _ensure_file_exists(self):
        path = Path(self.registry_file)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
                yaml.dump({'clients': []}, f)

    def _load(self) -> Dict:
        with open(self.registry_file, 'r') as f:
            return yaml.safe_load(f) or {'clients': []}

    def _save(self):
        with open(self.registry_file, 'w') as f:
            yaml.dump(self.data, f, default_flow_style=False, allow_unicode=True)

    def get_all_clients(self) -> List[Client]:
        clients = []
        for c in self.data.get('clients', []):
            clients.append(Client(**{k: v for k, v in c.items() if k in Client.__dataclass_fields__}))
        return clients

    def get_client(self, client_id: str) -> Optional[Client]:
        for c in self.data.get('clients', []):
            if c['client_id'] == client_id:
                return Client(**{k: v for k, v in c.items() if k in Client.__dataclass_fields__})
        return None

    def add_client(self, client_id: str, name: str, industry: str,
                   config_file: Optional[str] = None) -> bool:
        if self.get_client(client_id):
            return False

        if config_file is None:
            config_file = f"configs/clients/{client_id}_config.yaml"

        new_client = {
            'client_id': client_id,
            'name': name,
            'industry': industry,
            'status': 'active',
            'created_at': str(date.today()),
            'config_file': config_file
        }

        self.data.setdefault('clients', []).append(new_client)
        self._save()
        return True

    def update_client(self, client_id: str, **kwargs) -> bool:
        clients = self.data.get('clients', [])
        for i, c in enumerate(clients):
            if c['client_id'] == client_id:
                for key in ['name', 'industry', 'status', 'config_file']:
                    if key in kwargs:
                        clients[i][key] = kwargs[key]
                self._save()
                return True
        return False

    def delete_client(self, client_id: str) -> bool:
        clients = self.data.get('clients', [])
        original_count = len(clients)
        self.data['clients'] = [c for c in clients if c['client_id'] != client_id]

        if len(self.data['clients']) < original_count:
            self._save()
            return True
        return False

    def get_clients_by_status(self, status: str) -> List[Client]:
        return [c for c in self.get_all_clients() if c.status == status]
