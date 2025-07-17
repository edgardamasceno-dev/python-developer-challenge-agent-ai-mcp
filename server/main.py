from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from typing import Any, Optional, Literal, Dict, List
import inspect
from db import get_db
from tools import (
    buscar_veiculos, listar_marcas, listar_modelos, obter_range_anos, obter_range_precos, listar_cores_disponiveis, obter_range_km
)
from models import VehicleFilter
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

# --- JSON-RPC Models ---
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

# --- Exception Handler ---
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

# --- Root Endpoint ---
@app.get("/")
async def read_root():
    return {"message": "MCP server is running"}

# --- MCP Tool Definitions ---
MCP_METHODS = {
    "buscar_veiculos": buscar_veiculos,
    "listar_marcas": listar_marcas,
    "listar_modelos": listar_modelos,
    "obter_range_anos": obter_range_anos,
    "obter_range_precos": obter_range_precos,
    "listar_cores_disponiveis": listar_cores_disponiveis,
    "obter_range_km": obter_range_km,
}

# --- Dynamic Prompt Template Catalog ---
PROMPT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "search_intro": {
        "description": "Mensagem de introdução para iniciar a busca de veículos.",
        "arguments": [],
        "template": "Vamos encontrar o carro ideal para você. Quais características você procura?"
    },
    "filters_summary": {
        "description": "Resumo dos filtros aplicados na busca.",
        "arguments": [
            {"name": "filters", "description": "Dicionário dos filtros aplicados", "required": True}
        ],
        "template": "Buscando veículos com os seguintes filtros: {filters}"
    },
    "search_result_summary": {
        "description": "Resumo dos resultados encontrados na busca.",
        "arguments": [
            {"name": "vehicle_count", "description": "Quantidade de veículos encontrados", "required": True},
            {"name": "min_price", "description": "Preço mínimo", "required": False},
            {"name": "max_price", "description": "Preço máximo", "required": False},
            {"name": "min_km", "description": "Quilometragem mínima", "required": False},
            {"name": "max_km", "description": "Quilometragem máxima", "required": False}
        ],
        "template": "Foram encontrados {vehicle_count} veículos. Preço: R$ {min_price} a R$ {max_price}. Quilometragem: {min_km} a {max_km} km."
    },
    "no_results": {
        "description": "Mensagem exibida quando nenhum veículo é encontrado.",
        "arguments": [
            {"name": "filters", "description": "Dicionário dos filtros aplicados", "required": False}
        ],
        "template": "Nenhum veículo encontrado com os filtros informados: {filters}. Tente ajustar os critérios."
    },
    "vehicle_details": {
        "description": "Mensagem para detalhar um veículo específico.",
        "arguments": [
            {"name": "vehicle", "description": "Dicionário com os dados do veículo", "required": True}
        ],
        "template": "{vehicle[brand]} {vehicle[model]} {vehicle[year_manufacture]}, {vehicle[transmission]}, {vehicle[km]} km, R$ {vehicle[price]}, cor {vehicle[color]}"
    },
    "suggest_more_filters": {
        "description": "Sugere ao usuário adicionar mais filtros para refinar a busca.",
        "arguments": [
            {"name": "suggested_filters", "description": "Lista de filtros sugeridos", "required": False}
        ],
        "template": "Sua busca retornou muitos veículos. Que tal filtrar por {suggested_filters}?"
    },
    "action_confirmation": {
        "description": "Mensagem de confirmação após uma ação do usuário.",
        "arguments": [
            {"name": "action", "description": "Ação realizada", "required": True}
        ],
        "template": "Filtro aplicado: {action}"
    },
    "colors_list": {
        "description": "Mensagem para listar as cores disponíveis.",
        "arguments": [
            {"name": "colors", "description": "Lista de cores disponíveis", "required": True}
        ],
        "template": "Cores disponíveis: {colors}"
    },
    "brands_list": {
        "description": "Mensagem para listar as marcas disponíveis.",
        "arguments": [
            {"name": "brands", "description": "Lista de marcas disponíveis", "required": True}
        ],
        "template": "Marcas disponíveis: {brands}"
    },
    "models_list": {
        "description": "Mensagem para listar os modelos disponíveis.",
        "arguments": [
            {"name": "models", "description": "Lista de modelos disponíveis", "required": True}
        ],
        "template": "Modelos disponíveis: {models}"
    }
}


# --- Main MCP Endpoint ---
@app.post("/mcp")
async def mcp_endpoint(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        payload = await request.json()
        req = JSONRPCRequest(**payload)

        # --- Method: tools/list ---
        if req.method == "tools/list":
            tools = []
            for name, func in MCP_METHODS.items():
                docstring = inspect.getdoc(func) or f"No description available for {name}."
                input_schema = {"type": "object", "properties": {}}
                sig = inspect.signature(func)
                if "filters" in sig.parameters:
                    input_schema = VehicleFilter.model_json_schema()
                elif "brands" in sig.parameters:
                     input_schema = {
                        "type": "object",
                        "properties": {
                            "brands": {"type": "array", "items": {"type": "string"}}
                        },
                    }
                tools.append({"name": name, "description": docstring, "inputSchema": input_schema})
            return JSONResponse(content=JSONRPCResponse(result={"tools": tools}, id=req.id).dict(exclude_none=True))

        # --- Method: tools/call ---
        if req.method == "tools/call":
            name = req.params.get("name") if req.params else None
            arguments = req.params.get("arguments") if req.params else {}
            if name not in MCP_METHODS:
                raise HTTPException(status_code=404, detail=f"Tool not found: {name}")
            
            try:
                func = MCP_METHODS[name]
                sig = inspect.signature(func)
                
                # Prepare arguments based on function signature
                call_args = {}
                if "db" in sig.parameters:
                    call_args["db"] = db
                
                if "filters" in sig.parameters:
                    call_args["filters"] = VehicleFilter(**arguments)
                elif arguments:
                    # For other functions that take simple kwargs
                    for param_name, param_value in arguments.items():
                        if param_name in sig.parameters:
                            call_args[param_name] = param_value

                result = await func(**call_args)
                
                print(f"[MCP SERVER] Tool: {name} | Args: {arguments} | Result: {result}")
                return JSONResponse(content=JSONRPCResponse(result=result, id=req.id).dict(exclude_none=True))

            except Exception as e:
                print(f"[MCP SERVER] Tool: {name} | Args: {arguments} | ERROR: {e}")
                error = JSONRPCError(code=-32603, message="Internal error", data=str(e))
                return JSONResponse(status_code=500, content=JSONRPCResponse(error=error, id=req.id).dict(exclude_none=True))

        # --- Method: prompts/list ---
        if req.method == "prompts/list":
            prompts = [
                {"name": name, "description": data["description"], "arguments": data["arguments"]}
                for name, data in PROMPT_TEMPLATES.items()
            ]
            return JSONResponse(content=JSONRPCResponse(result={"prompts": prompts}, id=req.id).dict(exclude_none=True))

        # --- Method: prompts/get ---
        if req.method == "prompts/get":
            name = req.params.get("name") if req.params else None
            arguments = req.params.get("arguments") if req.params else {}
            
            template_data = PROMPT_TEMPLATES.get(name)
            if not template_data:
                error = JSONRPCError(code=-32602, message=f"Unknown prompt name: {name}")
                return JSONResponse(status_code=404, content=JSONRPCResponse(error=error, id=req.id).dict(exclude_none=True))

            try:
                # Simple string formatting for most cases
                prompt_text = template_data["template"].format(**arguments)
                
                # Special handling for templates with conditional logic
                if name == "search_result_summary":
                    price_str = f" Preço: R$ {arguments.get('min_price')} a R$ {arguments.get('max_price')}." if arguments.get('min_price') is not None else ""
                    km_str = f" Quilometragem: {arguments.get('min_km')} a {arguments.get('max_km')} km." if arguments.get('min_km') is not None else ""
                    prompt_text = f"Foram encontrados {arguments.get('vehicle_count', 0)} veículos.{price_str}{km_str}"

                result = {
                    "description": template_data["description"],
                    "messages": [{"role": "assistant", "content": prompt_text}]
                }
                return JSONResponse(content=JSONRPCResponse(result=result, id=req.id).dict(exclude_none=True))
            except KeyError as e:
                error = JSONRPCError(code=-32602, message=f"Missing required argument for prompt '{name}': {e}")
                return JSONResponse(status_code=400, content=JSONRPCResponse(error=error, id=req.id).dict(exclude_none=True))


        # --- Fallback for unknown methods ---
        error = JSONRPCError(code=-32601, message=f"Method not found: {req.method}")
        return JSONResponse(status_code=404, content=JSONRPCResponse(error=error, id=req.id).dict(exclude_none=True))

    except RequestValidationError as ve:
        raise ve # Re-raise to be handled by the exception handler
    except Exception as e:
        req_id = payload.get("id") if isinstance(payload, dict) else None
        error = JSONRPCError(code=-32603, message="Internal error", data=str(e))
        response = JSONRPCResponse(error=error, id=req_id)
        return JSONResponse(status_code=500, content=response.dict(exclude_none=True))
