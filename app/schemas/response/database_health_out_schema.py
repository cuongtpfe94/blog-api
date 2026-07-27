from pydantic import BaseModel


class DatabaseHealthResponse(BaseModel):
    """Response schema for database health check"""

    status: str
    database: str
