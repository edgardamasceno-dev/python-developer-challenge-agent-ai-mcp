-- Teste de integridade e performance do banco de dados veiculos_db

-- 1. Contagem total de veículos
SELECT COUNT(*) AS total_veiculos FROM veiculo;

-- 2. Busca textual (exemplo: veículos com 'preto' em marca, modelo, cor ou tipo_combustivel)
SELECT id, marca, modelo, cor, tipo_combustivel FROM veiculo WHERE ts_search @@ plainto_tsquery('portuguese', 'preto');

-- 3. Filtro por marca e modelo (usando índice composto)
SELECT COUNT(*) FROM veiculo WHERE marca = 'Volkswagen' AND modelo = 'Gol';

-- 4. Filtro por ano de fabricação (usando índice DESC)
SELECT COUNT(*) FROM veiculo WHERE ano_fabricacao >= 2020;

-- 5. Filtro por preço (usando índice)
SELECT COUNT(*) FROM veiculo WHERE preco BETWEEN 50000 AND 80000;

-- 6. Verificação dos índices existentes
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'veiculo';

-- 7. Verificação de integridade: checar se há veículos com preço <= 0 (não deve haver)
SELECT COUNT(*) AS veiculos_preco_invalido FROM veiculo WHERE preco <= 0;

-- 8. Verificação de integridade: checar se há veículos com quilometragem < 0 (não deve haver)
SELECT COUNT(*) AS veiculos_km_invalido FROM veiculo WHERE quilometragem < 0; 