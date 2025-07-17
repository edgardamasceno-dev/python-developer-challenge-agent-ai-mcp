from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from typing import Any, Optional

app = FastAPI()

class JSONRPCRequest(BaseModel):
    jsonrpc: str = Field(..., const=True, pattern="^2.0$")
    method: str
    params: Optional[Any] = None
    id: Any

class JSONRPCError(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None

class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[JSONRPCError] = None
    id: Any = None

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Retorna erro JSON-RPC padrão para erros de validação
    try:
        body = await request.json()
        req_id = body.get("id", None)
    except Exception:
        req_id = None
    return JSONResponse(
        status_code=400,
        content=JSONRPCResponse(
            error=JSONRPCError(code=-32600, message="Invalid Request", data=exc.errors()),
            id=req_id
        ).dict(exclude_none=True)
    )

@app.get("/")
async def read_root():
    """Healthcheck endpoint."""
    return {"message": "MCP server is running"}

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """Endpoint MCP JSON-RPC 2.0. Valida e responde conforme padrão MCP."""
    try:
        payload = await request.json()
        req = JSONRPCRequest(**payload)
        # Aqui entraria a lógica real do MCP
        response = JSONRPCResponse(result=f"MCP method '{req.method}' called successfully (mock)", id=req.id)
        return JSONResponse(content=response.dict(exclude_none=True))
    except RequestValidationError as ve:
        raise ve
    except Exception as e:
        # Erro interno padrão JSON-RPC
        req_id = payload.get("id") if isinstance(payload, dict) else None
        error = JSONRPCError(code=-32603, message="Internal error", data=str(e))
        response = JSONRPCResponse(error=error, id=req_id)
        return JSONResponse(status_code=500, content=response.dict(exclude_none=True)) 