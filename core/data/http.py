from dataclasses import dataclass, field
from typing import Dict, Optional, Union, Any
from enum import Enum
import json

class HttpMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"

@dataclass
class HttpRequest:
    url: str
    method: HttpMethod = HttpMethod.GET
    headers: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, str] = field(default_factory=dict)
    body: Optional[Union[Dict[str, Any], str, bytes]] = None
    timeout: float = 30.0
    
    def add_header(self, key: str, value: str) -> None:
        self.headers[key] = value
    
    def add_param(self, key: str, value: str) -> None:
        self.params[key] = value
    
    def set_json_body(self, data: Dict[str, Any]) -> None:
        self.body = data
        self.add_header("Content-Type", "application/json")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "method": self.method.value,
            "headers": self.headers,
            "params": self.params,
            "body": self.body,
            "timeout": self.timeout
        }

@dataclass
class HttpResponse:
    status_code: int
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[Union[Dict[str, Any], str, bytes]] = None
    elapsed_time: float = 0.0
    request: Optional[HttpRequest] = None
    
    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300
    
    @property
    def is_redirect(self) -> bool:
        return 300 <= self.status_code < 400
    
    @property
    def is_client_error(self) -> bool:
        return 400 <= self.status_code < 500
    
    @property
    def is_server_error(self) -> bool:
        return 500 <= self.status_code < 600
    
    def json(self) -> Dict[str, Any]:
        if isinstance(self.body, dict):
            return self.body
        elif isinstance(self.body, str):
            return json.loads(self.body)
        elif isinstance(self.body, bytes):
            return json.loads(self.body.decode('utf-8'))
        else:
            raise ValueError("Response body cannot be converted to JSON")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status_code": self.status_code,
            "headers": self.headers,
            "body": self.body,
            "elapsed_time": self.elapsed_time,
            "request": self.request.to_dict() if self.request else None
        }