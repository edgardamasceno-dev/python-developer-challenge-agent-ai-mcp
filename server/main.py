from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from typing import Any, Optional, Literal
from db import get_db
from tools import (
    buscar_veiculos, listar_marcas, listar_modelos, obter_range_anos, obter_range_precos, listar_cores_disponiveis, obter_range_km
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
    "listar_cores_disponiveis": listar_cores_disponiveis,
    "obter_range_km": obter_range_km,
}

@app.post("/mcp")
async def mcp_endpoint(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        payload = await request.json()
        req = JSONRPCRequest(**payload)
        # Suporte ao método tools/list (MCP discovery)
        if req.method == "tools/list":
            # Definição das tools no padrão MCP
            tools = [
                {
                    "name": "buscar_veiculos",
                    "description": "Search vehicles in the database with advanced filters.\n\nYou can filter by any combination of the following attributes:\n- brand (string): Vehicle brand.\n- model (string): Vehicle model.\n- year_min/year_max (integer): Manufacturing year range.\n- price_min/price_max (number): Price range.\n- km_min/km_max (integer): Mileage range.\n- fuel_type (string): Fuel type.\n- color (string): Color.\n- doors (integer): Number of doors.\n- transmission (string): Transmission type.\n- search_text (string): Free text search.\n\nExample 1: Find Volkswagens from 2020 or newer up to R$80,000:\n{\n  \"brand\": \"Volkswagen\",\n  \"year_min\": 2020,\n  \"price_max\": 80000\n}\n\nExample 2: Find red Honda cars with automatic transmission:\n{\n  \"brand\": \"Honda\",\n  \"color\": \"Vermelho\",\n  \"transmission\": \"Automática\"\n}\n\nYou can combine any filters as needed.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "search_text": {"type": "string", "description": "Free text search"},
                            "brand": {"type": "string"},
                            "model": {"type": "string"},
                            "year_min": {"type": "integer"},
                            "year_max": {"type": "integer"},
                            "price_min": {"type": "number"},
                            "price_max": {"type": "number"},
                            "km_min": {"type": "integer"},
                            "km_max": {"type": "integer"},
                            "fuel_type": {"type": "string"},
                            "color": {"type": "string"},
                            "doors": {"type": "integer"},
                            "transmission": {"type": "string"}
                        },
                    },
                },
                {
                    "name": "listar_marcas",
                    "description": "List all unique vehicle brands available.",
                    "inputSchema": {"type": "object", "properties": {}}
                },
                {
                    "name": "listar_modelos",
                    "description": "List vehicle models, optionally filtered by brands.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "brands": {"type": "array", "items": {"type": "string"}}
                        },
                    },
                },
                {
                    "name": "obter_range_anos",
                    "description": "Get the min and max manufacturing years of available vehicles.",
                    "inputSchema": {"type": "object", "properties": {}}
                },
                {
                    "name": "obter_range_precos",
                    "description": "Get the min and max prices of available vehicles.",
                    "inputSchema": {"type": "object", "properties": {}}
                },
                {
                    "name": "listar_cores_disponiveis",
                    "description": "List all unique vehicle colors available.",
                    "inputSchema": {"type": "object", "properties": {}}
                },
                {
                    "name": "obter_range_km",
                    "description": "Get the min and max mileage (quilometragem) of available vehicles.",
                    "inputSchema": {"type": "object", "properties": {}}
                },
            ]
            return JSONResponse(content=JSONRPCResponse(result={"tools": tools, "nextCursor": None}, id=req.id).dict(exclude_none=True))
        # Suporte ao método prompts/list (MCP)
        if req.method == "prompts/list":
            prompts = [
                {
                    "name": "car_search_intro",
                    "description": "Prompt de introdução para busca de veículos.",
                    "arguments": [
                        {"name": "user_name", "description": "Nome do usuário", "required": False}
                    ]
                },
                {
                    "name": "car_search_result",
                    "description": "Prompt para exibir resultados de busca de veículos.",
                    "arguments": [
                        {"name": "vehicle_count", "description": "Quantidade de veículos encontrados", "required": True}
                    ]
                }
            ]
            return JSONResponse(content=JSONRPCResponse(result={"prompts": prompts, "nextCursor": None}, id=req.id).dict(exclude_none=True))
        # Suporte ao método prompts/get (MCP)
        if req.method == "prompts/get":
            name = req.params.get("name") if req.params else None
            arguments = req.params.get("arguments") if req.params else {}
            if name == "car_search_intro":
                user_name = arguments.get("user_name", "")
                prompt_text = f"Olá{', ' + user_name if user_name else ''}! Vamos encontrar o carro ideal para você. Me conte o que procura!"
                return JSONResponse(content=JSONRPCResponse(result={"description": "Prompt de introdução", "messages": [{"role": "assistant", "content": prompt_text}]}, id=req.id).dict(exclude_none=True))
            elif name == "car_search_result":
                vehicle_count = arguments.get("vehicle_count", 0)
                prompt_text = f"Encontrei {vehicle_count} veículo(s) compatível(is) com sua busca. Veja os detalhes abaixo."
                return JSONResponse(content=JSONRPCResponse(result={"description": "Prompt de resultado", "messages": [{"role": "assistant", "content": prompt_text}]}, id=req.id).dict(exclude_none=True))
            else:
                return JSONResponse(content=JSONRPCResponse(error=JSONRPCError(code=-32602, message="Unknown prompt name"), id=req.id).dict(exclude_none=True))
        # Suporte ao método tools/call (MCP padrão)
        if req.method == "tools/call":
            name = req.params.get("name") if req.params else None
            arguments = req.params.get("arguments") if req.params else {}
            if name not in MCP_METHODS:
                return JSONResponse(
                    status_code=400,
                    content=JSONRPCResponse(
                        error=JSONRPCError(code=-32601, message=f"Tool not found: {name}"),
                        id=req.id
                    ).dict(exclude_none=True)
                )
            # Chama a tool correspondente
            try:
                if name == "buscar_veiculos":
                    filters = VehicleFilter(**arguments)
                    result = await MCP_METHODS[name](db, filters)
                    print(f"[MCP SERVER] Tool: {name} | Args: {arguments} | Result: {result}")
                    return JSONResponse(content=JSONRPCResponse(result=[r.dict() for r in result], id=req.id).dict(exclude_none=True))
                elif name == "listar_marcas":
                    result = await MCP_METHODS[name](db)
                    print(f"[MCP SERVER] Tool: {name} | Args: {arguments} | Result: {result}")
                    return JSONResponse(content=JSONRPCResponse(result=result.dict(), id=req.id).dict(exclude_none=True))
                elif name == "listar_modelos":
                    brands = arguments.get("brands")
                    result = await MCP_METHODS[name](db, brands)
                    print(f"[MCP SERVER] Tool: {name} | Args: {arguments} | Result: {result}")
                    return JSONResponse(content=JSONRPCResponse(result=result.dict(), id=req.id).dict(exclude_none=True))
                elif name == "obter_range_anos":
                    result = await MCP_METHODS[name](db)
                    print(f"[MCP SERVER] Tool: {name} | Args: {arguments} | Result: {result}")
                    return JSONResponse(content=JSONRPCResponse(result=result.dict(), id=req.id).dict(exclude_none=True))
                elif name == "obter_range_precos":
                    result = await MCP_METHODS[name](db)
                    print(f"[MCP SERVER] Tool: {name} | Args: {arguments} | Result: {result}")
                    return JSONResponse(content=JSONRPCResponse(result=result.dict(), id=req.id).dict(exclude_none=True))
                elif name == "listar_cores_disponiveis":
                    result = await MCP_METHODS[name](db)
                    print(f"[MCP SERVER] Tool: {name} | Args: {arguments} | Result: {result}")
                    return JSONResponse(content=JSONRPCResponse(result=result, id=req.id).dict(exclude_none=True))
                elif name == "obter_range_km":
                    result = await MCP_METHODS[name](db)
                    print(f"[MCP SERVER] Tool: {name} | Args: {arguments} | Result: {result}")
                    return JSONResponse(content=JSONRPCResponse(result=result, id=req.id).dict(exclude_none=True))
                else:
                    return JSONResponse(
                        status_code=400,
                        content=JSONRPCResponse(
                            error=JSONRPCError(code=-32601, message=f"Tool not found: {name}"),
                            id=req.id
                        ).dict(exclude_none=True)
                    )
            except Exception as e:
                print(f"[MCP SERVER] Tool: {name} | Args: {arguments} | ERROR: {e}")
                return JSONResponse(
                    status_code=500,
                    content=JSONRPCResponse(
                        error=JSONRPCError(code=-32603, message=f"Internal error: {e}"),
                        id=req.id
                    ).dict(exclude_none=True)
                )
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