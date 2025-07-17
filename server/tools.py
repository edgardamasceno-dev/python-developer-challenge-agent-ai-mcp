from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict
from models import Veiculo, VehicleFilter, VehicleResult, BrandListOut, ModelListOut, YearRangeOut, PriceRangeOut, KmRangeOut

async def buscar_veiculos(db: AsyncSession, filters: VehicleFilter) -> List[VehicleResult]:
    query = select(Veiculo)
    if filters.brand:
        query = query.where(Veiculo.marca == filters.brand)
    if filters.model:
        query = query.where(Veiculo.modelo == filters.model)
    if filters.year_min:
        query = query.where(Veiculo.ano_fabricacao >= filters.year_min)
    if filters.year_max:
        query = query.where(Veiculo.ano_fabricacao <= filters.year_max)
    if filters.price_min:
        query = query.where(Veiculo.preco >= filters.price_min)
    if filters.price_max:
        query = query.where(Veiculo.preco <= filters.price_max)
    if filters.km_min:
        query = query.where(Veiculo.quilometragem >= filters.km_min)
    if filters.km_max:
        query = query.where(Veiculo.quilometragem <= filters.km_max)
    if filters.fuel_type:
        query = query.where(Veiculo.tipo_combustivel == filters.fuel_type)
    if filters.color:
        query = query.where(Veiculo.cor == filters.color)
    if filters.doors:
        query = query.where(Veiculo.numero_portas == filters.doors)
    if filters.transmission:
        query = query.where(Veiculo.tipo_transmissao == filters.transmission)
    result = await db.execute(query)
    veiculos = result.scalars().all()
    return [VehicleResult.from_orm(v) for v in veiculos]

async def listar_marcas(db: AsyncSession) -> BrandListOut:
    result = await db.execute(select(distinct(Veiculo.marca)))
    brands = [row[0] for row in result.all()]
    return BrandListOut(brands=brands)

async def listar_modelos(db: AsyncSession, brands: Optional[List[str]] = None) -> ModelListOut:
    query = select(distinct(Veiculo.modelo))
    if brands:
        query = query.where(Veiculo.marca.in_(brands))
    result = await db.execute(query)
    models = [row[0] for row in result.all()]
    return ModelListOut(models=models)

async def obter_range_anos(db: AsyncSession) -> YearRangeOut:
    result = await db.execute(select(func.min(Veiculo.ano_fabricacao), func.max(Veiculo.ano_fabricacao)))
    min_year, max_year = result.one()
    return YearRangeOut(min_year=min_year, max_year=max_year)

async def obter_range_precos(db: AsyncSession) -> PriceRangeOut:
    result = await db.execute(select(func.min(Veiculo.preco), func.max(Veiculo.preco)))
    min_price, max_price = result.one()
    return PriceRangeOut(min_price=float(min_price), max_price=float(max_price))

async def obter_range_km(db: AsyncSession) -> KmRangeOut:
    from sqlalchemy import func
    result = await db.execute(select(func.min(Veiculo.quilometragem), func.max(Veiculo.quilometragem)))
    min_km, max_km = result.one()
    return KmRangeOut(min_km=int(min_km), max_km=int(max_km))

async def listar_cores_disponiveis(db: AsyncSession) -> Dict[str, List[str]]:
    result = await db.execute(select(distinct(Veiculo.cor)))
    cores = [row[0] for row in result.all()]
    return {"cores": cores} 