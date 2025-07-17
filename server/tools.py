from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict
from models import Veiculo, VehicleFilter, VehicleResult, BrandListOut, ModelListOut, YearRangeOut, PriceRangeOut, KmRangeOut, ColorListOut

async def buscar_veiculos(db: AsyncSession, filters: VehicleFilter) -> List[VehicleResult]:
    """
    Busca e filtra veículos no catálogo com base em múltiplos critérios.

    Use esta ferramenta para responder a perguntas detalhadas do usuário, como
    'encontre carros da Toyota, vermelhos, com 4 portas' ou 'procure por carros
    entre R$50.000 e R$80.000'.

    Args:
        db: A sessão da base de dados assíncrona.
        filters: Um objeto com múltiplos atributos opcionais para filtrar a busca,
                 incluindo marca, modelo, faixa de ano, faixa de preço, etc.

    Returns:
        Uma lista de objetos de veículos, cada um contendo informações detalhadas
        do veículo que corresponde aos critérios de busca.
    """
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
    """
    Obtém uma lista de todas as marcas de veículos disponíveis no catálogo.

    Use esta ferramenta para preencher opções de filtro para o usuário ou para
    responder a perguntas como 'quais marcas vocês têm?'.

    Args:
        db: A sessão da base de dados assíncrona.

    Returns:
        Um objeto contendo uma lista de strings, onde cada string é um nome de marca único.
    """
    result = await db.execute(select(distinct(Veiculo.marca)))
    brands = [row[0] for row in result.all()]
    return BrandListOut(brands=brands)

async def listar_modelos(db: AsyncSession, brands: Optional[List[str]] = None) -> ModelListOut:
    """
    Obtém uma lista de todos os modelos de veículos disponíveis, opcionalmente filtrada por marca.

    Use esta ferramenta para encontrar modelos disponíveis ou para popular um filtro de modelos,
    especialmente depois que o usuário já selecionou uma ou mais marcas.

    Args:
        db: A sessão da base de dados assíncrona.
        brands: Uma lista opcional de nomes de marcas para filtrar os modelos.

    Returns:
        Um objeto contendo uma lista de strings, onde cada string é um nome de modelo único.
    """
    query = select(distinct(Veiculo.modelo))
    if brands:
        query = query.where(Veiculo.marca.in_(brands))
    result = await db.execute(query)
    models = [row[0] for row in result.all()]
    return ModelListOut(models=models)

async def obter_range_anos(db: AsyncSession) -> YearRangeOut:
    """
    Encontra o ano de fabricação mínimo e máximo de todos os veículos no inventário.

    Ideal para configurar os limites de um controle de filtro de ano (como um slider
    ou campos de input min/max).

    Args:
        db: A sessão da base de dados assíncrona.

    Returns:
        Um objeto contendo o ano mínimo (min_year) e máximo (max_year).
    """
    result = await db.execute(select(func.min(Veiculo.ano_fabricacao), func.max(Veiculo.ano_fabricacao)))
    min_year, max_year = result.one()
    return YearRangeOut(min_year=min_year, max_year=max_year)

async def obter_range_precos(db: AsyncSession) -> PriceRangeOut:
    """
    Encontra o preço mínimo e máximo de todos os veículos no inventário.

    Ideal para configurar os limites de um controle de filtro de preço (como um slider
    ou campos de input min/max).

    Args:
        db: A sessão da base de dados assíncrona.

    Returns:
        Um objeto contendo o preço mínimo (min_price) e máximo (max_price).
    """
    result = await db.execute(select(func.min(Veiculo.preco), func.max(Veiculo.preco)))
    min_price, max_price = result.one()
    return PriceRangeOut(min_price=float(min_price), max_price=float(max_price))

async def obter_range_km(db: AsyncSession) -> KmRangeOut:
    """
    Encontra a quilometragem mínima e máxima de todos os veículos no inventário.

    Ideal para configurar os limites de um controle de filtro de quilometragem (como um
    slider ou campos de input min/max).

    Args:
        db: A sessão da base de dados assíncrona.

    Returns:
        Um objeto contendo a quilometragem mínima (min_km) e máxima (max_km).
    """
    from sqlalchemy import func
    result = await db.execute(select(func.min(Veiculo.quilometragem), func.max(Veiculo.quilometragem)))
    min_km, max_km = result.one()
    return KmRangeOut(min_km=int(min_km), max_km=int(max_km))

async def listar_cores_disponiveis(db: AsyncSession) -> ColorListOut:
    """
    Obtém uma lista de todas as cores de veículos únicas disponíveis no catálogo.

    Use para preencher um seletor de cores ou responder a perguntas sobre as
    cores em estoque.

    Args:
        db: A sessão da base de dados assíncrona.

    Returns:
        Um objeto contendo uma lista de strings, onde cada string é um nome de cor único.
    """
    result = await db.execute(select(distinct(Veiculo.cor)))
    cores = [row[0] for row in result.all()]
    return ColorListOut(cores=cores)