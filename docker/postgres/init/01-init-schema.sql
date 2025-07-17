CREATE EXTENSION IF NOT EXISTS unaccent;

CREATE TABLE IF NOT EXISTS veiculo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid_v7(),
    marca VARCHAR(100) NOT NULL,
    modelo VARCHAR(100) NOT NULL,
    ano_fabricacao INT NOT NULL,
    ano_modelo INT NOT NULL,
    motorizacao NUMERIC(2, 1) NOT NULL,
    tipo_combustivel VARCHAR(50) NOT NULL,
    cor VARCHAR(50) NOT NULL,
    quilometragem INT NOT NULL CHECK (quilometragem >= 0),
    numero_portas INT NOT NULL CHECK (numero_portas IN (2, 3, 4, 5)),
    tipo_transmissao VARCHAR(50) NOT NULL,
    preco NUMERIC(10, 2) NOT NULL CHECK (preco > 0),
    data_criacao TIMESTAMPTZ NOT NULL DEFAULT (now() at time zone 'utc'),
    ts_search TSVECTOR GENERATED ALWAYS AS (
        to_tsvector('portuguese', unaccent(marca) || ' ' || unaccent(modelo) || ' ' || unaccent(cor) || ' ' || unaccent(tipo_combustivel))
    ) STORED,
    CONSTRAINT ano_valido CHECK (ano_fabricacao >= 1990 AND ano_modelo >= ano_fabricacao AND ano_modelo <= EXTRACT(YEAR FROM now()) + 1)
);

CREATE INDEX IF NOT EXISTS idx_veiculo_marca_modelo ON veiculo (marca, modelo);
CREATE INDEX IF NOT EXISTS idx_veiculo_ano_fabricacao ON veiculo (ano_fabricacao DESC);
CREATE INDEX IF NOT EXISTS idx_veiculo_preco ON veiculo (preco);
CREATE INDEX IF NOT EXISTS idx_veiculo_ts_search ON veiculo USING GIN(ts_search); 