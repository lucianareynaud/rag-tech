from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class QueryRequest(BaseModel):
    user_id: Optional[str] = Field(default=None)
    query: str = Field(min_length=1)

class Source(BaseModel):
    doc_id: str
    score: float

class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]
    meta: Dict[str, object] = {}
