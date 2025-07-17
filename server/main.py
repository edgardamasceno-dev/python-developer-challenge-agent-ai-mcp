from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from typing import Any, Optional, Literal
from db import get_db
from tools import (
    buscar_veiculos, listar_marcas, listar_modelos, obter_range_anos, obter_range_precos
)
from models import VehicleFilter
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

class JSONRPCRequest(BaseModel):
    jsonrpc: Literal["2.0"]
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
    return {"message": "MCP server is running"}

MCP_METHODS = {
    "buscar_veiculos": buscar_veiculos,
    "listar_marcas": listar_marcas,
    "listar_modelos": listar_modelos,
    "obter_range_anos": obter_range_anos,
    "obter_range_precos": obter_range_precos,
}

@app.post("/mcp")
async def mcp_endpoint(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        payload = await request.json()
        req = JSONRPCRequest(**payload)
        if req.method not in MCP_METHODS:
            return JSONResponse(
                status_code=400,
                content=JSONRPCResponse(
                    error=JSONRPCError(code=-32601, message=f"Method not found: {req.method}"),
                    id=req.id
                ).dict(exclude_none=True)
            )
        # Dispatcher para cada método
        if req.method == "buscar_veiculos":
            filters = VehicleFilter(**(req.params or {}))
            result = await MCP_METHODS[req.method](db, filters)
            return JSONResponse(content=JSONRPCResponse(result=[r.dict() for r in result], id=req.id).dict(exclude_none=True))
        elif req.method == "listar_marcas":
            result = await MCP_METHODS[req.method](db)
            return JSONResponse(content=JSONRPCResponse(result=result.dict(), id=req.id).dict(exclude_none=True))
        elif req.method == "listar_modelos":
            brands = req.params.get("brands") if req.params else None
            result = await MCP_METHODS[req.method](db, brands)
            return JSONResponse(content=JSONRPCResponse(result=result.dict(), id=req.id).dict(exclude_none=True))
        elif req.method == "obter_range_anos":
            result = await MCP_METHODS[req.method](db)
            return JSONResponse(content=JSONRPCResponse(result=result.dict(), id=req.id).dict(exclude_none=True))
        elif req.method == "obter_range_precos":
            result = await MCP_METHODS[req.method](db)
            return JSONResponse(content=JSONRPCResponse(result=result.dict(), id=req.id).dict(exclude_none=True))
        else:
            return JSONResponse(
                status_code=400,
                content=JSONRPCResponse(
                    error=JSONRPCError(code=-32601, message=f"Method not found: {req.method}"),
                    id=req.id
                ).dict(exclude_none=True)
            )
    except RequestValidationError as ve:
        raise ve
    except Exception as e:
        req_id = payload.get("id") if isinstance(payload, dict) else None
        error = JSONRPCError(code=-32603, message="Internal error", data=str(e))
        response = JSONRPCResponse(error=error, id=req_id)
        return JSONResponse(status_code=500, content=response.dict(exclude_none=True)) 