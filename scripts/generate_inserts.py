import random
import math
from faker import Faker
from rich.progress import track
from pathlib import Path

fake = Faker('pt_BR')
Faker.seed(42)
random.seed(42)

NUM_VEHICLES = 250
CURRENT_YEAR = 2025
OUTPUT_DIR = Path(__file__).parent.parent / "docker" / "postgres" / "init"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "02-populate-data.sql"

brands_models = {
    'Ford': ['Ka', 'Fiesta', 'Focus', 'EcoSport', 'Ranger'],
    'Chevrolet': ['Onix', 'Prisma', 'Cruze', 'S10', 'Tracker'],
    'Volkswagen': ['Gol', 'Polo', 'Virtus', 'T-Cross', 'Nivus', 'Saveiro'],
    'Toyota': ['Corolla', 'Hilux', 'Yaris', 'RAV4'],
    'Honda': ['Civic', 'Fit', 'HR-V', 'WR-V', 'City'],
    'Fiat': ['Mobi', 'Argo', 'Toro', 'Strada', 'Pulse'],
    'Hyundai': ['HB20', 'Creta', 'HB20S'],
    'Jeep': ['Renegade', 'Compass', 'Commander'],
    'Renault': ['Kwid', 'Sandero', 'Logan', 'Duster', 'Captur']
}
fuel_types = ['Flex', 'Gasolina', 'Diesel', 'Etanol', 'Híbrido']
transmission_types = ['Manual', 'Automática', 'CVT', 'Automatizada']
popular_colors = ['Preto', 'Branco', 'Prata', 'Cinza', 'Vermelho', 'Azul']
doors = [2, 4]
engine_sizes = [1.0, 1.3, 1.4, 1.5, 1.6, 1.8, 2.0]

def generate_price_and_km(year):
    age = CURRENT_YEAR - year
    base_price = 120000 * math.exp(-age * 0.15)
    final_price = random.uniform(base_price * 0.8, base_price * 1.2)
    base_km = age * 15000
    final_km = max(0, random.uniform(base_km * 0.7, base_km * 1.3))
    return round(final_price, 2), int(final_km)

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write("INSERT INTO veiculo (marca, modelo, ano_fabricacao, ano_modelo, motorizacao, tipo_combustivel, cor, quilometragem, numero_portas, tipo_transmissao, preco) VALUES\n")
    values = []
    for _ in track(range(NUM_VEHICLES), description="Generating vehicle data..."):
        brand = random.choice(list(brands_models.keys()))
        model = random.choice(brands_models[brand])
        year_manufacture = random.randint(2010, CURRENT_YEAR - 1)
        year_model = random.choice([year_manufacture, year_manufacture + 1])
        price, km = generate_price_and_km(year_manufacture)

        values.append(
            f"('{brand}', '{model}', {year_manufacture}, {year_model}, "
            f"{random.choice(engine_sizes)}, '{random.choice(fuel_types)}', "
            f"'{random.choice(popular_colors)}', {km}, {random.choice(doors)}, "
            f"'{random.choice(transmission_types)}', {price})"
        )
    f.write(',\n'.join(values) + ';\n')

print(f"\nFile {OUTPUT_FILE} generated successfully.") 