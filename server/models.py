from sqlalchemy import Column, String, Integer, Numeric, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid

Base = declarative_base()

class Veiculo(Base):
    __tablename__ = "veiculo"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    marca = Column(String(100), nullable=False)
    modelo = Column(String(100), nullable=False)
    ano_fabricacao = Column(Integer, nullable=False)
    ano_modelo = Column(Integer, nullable=False)
    motorizacao = Column(Numeric(2, 1), nullable=False)
    tipo_combustivel = Column(String(50), nullable=False)
    cor = Column(String(50), nullable=False)
    quilometragem = Column(Integer, nullable=False)
    numero_portas = Column(Integer, nullable=False)
    tipo_transmissao = Column(String(50), nullable=False)
    preco = Column(Numeric(10, 2), nullable=False)
    data_criacao = Column(TIMESTAMP(timezone=True), server_default=text("now() at time zone 'utc'"))

class VehicleFilter(BaseModel):
    search_text: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    km_min: Optional[int] = None
    km_max: Optional[int] = None
    fuel_type: Optional[str] = None
    color: Optional[str] = None
    doors: Optional[int] = None
    transmission: Optional[str] = None

class VehicleResult(BaseModel):
    id: str
    brand: str
    model: str
    year_manufacture: int
    year_model: int
    engine: float
    fuel_type: str
    color: str
    km: int
    doors: int
    transmission: str
    price: float

    @classmethod
    def from_orm(cls, v: Veiculo):
        return cls(
            id=str(v.id),
            brand=v.marca,
            model=v.modelo,
            year_manufacture=v.ano_fabricacao,
            year_model=v.ano_modelo,
            engine=float(v.motorizacao),
            fuel_type=v.tipo_combustivel,
            color=v.cor,
            km=v.quilometragem,
            doors=v.numero_portas,
            transmission=v.tipo_transmissao,
            price=float(v.preco),
        )

class BrandListOut(BaseModel):
    brands: List[str]

class ModelListOut(BaseModel):
    models: List[str]

class YearRangeOut(BaseModel):
    min_year: int
    max_year: int

class PriceRangeOut(BaseModel):
    min_price: float
    max_price: float

class ColorListOut(BaseModel):
    cores: List[str]

class KmRangeOut(BaseModel):
    min_km: int
    max_km: int 