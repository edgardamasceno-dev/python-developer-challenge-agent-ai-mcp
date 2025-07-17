CREATE EXTENSION IF NOT EXISTS unaccent;

CREATE TABLE IF NOT EXISTS veiculo (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
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
    ts_search TSVECTOR,
    CONSTRAINT ano_valido CHECK (ano_fabricacao >= 1990 AND ano_modelo >= ano_fabricacao AND ano_modelo <= EXTRACT(YEAR FROM now()) + 1)
);

CREATE OR REPLACE FUNCTION veiculo_tsvector_trigger() RETURNS trigger AS $$
BEGIN
  NEW.ts_search := to_tsvector('portuguese', unaccent(NEW.marca) || ' ' || unaccent(NEW.modelo) || ' ' || unaccent(NEW.cor) || ' ' || unaccent(NEW.tipo_combustivel));
  RETURN NEW;
END
$$ LANGUAGE plpgsql;

CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
    ON veiculo FOR EACH ROW EXECUTE FUNCTION veiculo_tsvector_trigger();

CREATE INDEX IF NOT EXISTS idx_veiculo_marca_modelo ON veiculo (marca, modelo);
CREATE INDEX IF NOT EXISTS idx_veiculo_ano_fabricacao ON veiculo (ano_fabricacao DESC);
CREATE INDEX IF NOT EXISTS idx_veiculo_preco ON veiculo (preco);
CREATE INDEX IF NOT EXISTS idx_veiculo_ts_search ON veiculo USING GIN(ts_search); 