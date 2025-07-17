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

# Sugestões de textos para cada prompt MCP:
# search_intro: "Vamos encontrar o carro ideal para você. Quais características você procura?"
# filters_summary: "Buscando veículos com os seguintes filtros: {filters}"
# search_result_summary: "Foram encontrados {vehicle_count} veículos. Preço: R$ {min_price} a R$ {max_price}. Quilometragem: {min_km} a {max_km} km."
# no_results: "Nenhum veículo encontrado com os filtros informados: {filters}. Tente ajustar os critérios."
# vehicle_details: "{vehicle['brand']} {vehicle['model']} {vehicle['year_manufacture']}, {vehicle['transmission']}, {vehicle['km']} km, R$ {vehicle['price']}, cor {vehicle['color']}"
# suggest_more_filters: "Sua busca retornou muitos veículos. Que tal filtrar por ano, preço ou cor?"
# action_confirmation: "Filtro aplicado: {action}"

@app.post("/mcp")
async def mcp_endpoint(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        payload = await request.json()
        req = JSONRPCRequest(**payload)
        if req.method == "tools/list":
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
                    "description": "List vehicle models. If you want models from specific brands, provide the 'brands' parameter as a list of brand names. To list models from all brands, omit the 'brands' parameter or pass an empty list.\n\nExamples:\n- All models: {}\n- Only Ford and Toyota: {\"brands\": [\"Ford\", \"Toyota\"]}",
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
                    "description": "Get the min and max mileage (quilometragem) of available vehicles.\n\nReturns an object with min_km and max_km.\nExample: {\n  \"min_km\": 10827,\n  \"max_km\": 285427\n}",
                    "inputSchema": {"type": "object", "properties": {}}
                },
            ]
            return JSONResponse(content=JSONRPCResponse(result={"tools": tools, "nextCursor": None}, id=req.id).dict(exclude_none=True))
        if req.method == "prompts/list":
            prompts = [
                {
                    "name": "search_intro",
                    "description": "Mensagem de introdução para iniciar a busca de veículos.",
                    "arguments": []
                },
                {
                    "name": "filters_summary",
                    "description": "Resumo dos filtros aplicados na busca.",
                    "arguments": [
                        {"name": "filters", "description": "Dicionário dos filtros aplicados", "required": True}
                    ]
                },
                {
                    "name": "search_result_summary",
                    "description": "Resumo dos resultados encontrados na busca.",
                    "arguments": [
                        {"name": "vehicle_count", "description": "Quantidade de veículos encontrados", "required": True},
                        {"name": "min_price", "description": "Preço mínimo", "required": False},
                        {"name": "max_price", "description": "Preço máximo", "required": False},
                        {"name": "min_km", "description": "Quilometragem mínima", "required": False},
                        {"name": "max_km", "description": "Quilometragem máxima", "required": False}
                    ]
                },
                {
                    "name": "no_results",
                    "description": "Mensagem exibida quando nenhum veículo é encontrado.",
                    "arguments": [
                        {"name": "filters", "description": "Dicionário dos filtros aplicados", "required": False}
                    ]
                },
                {
                    "name": "vehicle_details",
                    "description": "Mensagem para detalhar um veículo específico.",
                    "arguments": [
                        {"name": "vehicle", "description": "Dicionário com os dados do veículo", "required": True}
                    ]
                },
                {
                    "name": "suggest_more_filters",
                    "description": "Sugere ao usuário adicionar mais filtros para refinar a busca.",
                    "arguments": [
                        {"name": "suggested_filters", "description": "Lista de filtros sugeridos", "required": False}
                    ]
                },
                {
                    "name": "action_confirmation",
                    "description": "Mensagem de confirmação após uma ação do usuário.",
                    "arguments": [
                        {"name": "action", "description": "Ação realizada", "required": True}
                    ]
                }
            ]
            return JSONResponse(content=JSONRPCResponse(result={"prompts": prompts, "nextCursor": None}, id=req.id).dict(exclude_none=True))
        if req.method == "prompts/get":
            name = req.params.get("name") if req.params else None
            arguments = req.params.get("arguments") if req.params else {}
            if name == "car_search_intro":
                user_name = arguments.get("user_name", "")
                prompt_text = f"Olá{', ' + user_name if user_name else ''}! Vamos encontrar o carro ideal para você. Me conte o que procura!"
                return JSONResponse(content=JSONRPCResponse(result={"description": "Prompt de introdução", "messages": [{"role": "assistant", "content": prompt_text}]}, id=req.id).dict(exclude_none=True))
            elif name == "car_search_result":
                vehicle_count = arguments.get("vehicle_count", 0)
                min_km = arguments.get("min_km")
                max_km = arguments.get("max_km")
                if min_km is not None and max_km is not None:
                    prompt_text = f"Encontrei {vehicle_count} veículo(s) compatível(is) com sua busca. A quilometragem dos veículos disponíveis varia de {min_km:,} km a {max_km:,} km. Veja os detalhes abaixo."
                else:
                    prompt_text = f"Encontrei {vehicle_count} veículo(s) compatível(is) com sua busca. Veja os detalhes abaixo."
                return JSONResponse(content=JSONRPCResponse(result={"description": "Prompt de resultado", "messages": [{"role": "assistant", "content": prompt_text}]}, id=req.id).dict(exclude_none=True))
            else:
                return JSONResponse(content=JSONRPCResponse(error=JSONRPCError(code=-32602, message="Unknown prompt name"), id=req.id).dict(exclude_none=True))
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