WITH 
dicionario_categoria AS (
    SELECT
        chave AS chave_categoria,
        valor AS descricao_categoria
    FROM `basedosdados.br_me_caged.dicionario`
    WHERE
        TRUE
        AND nome_coluna = 'categoria'
        AND id_tabela = 'microdados_movimentacao'
),
dicionario_grau_instrucao AS (
    SELECT
        chave AS chave_grau_instrucao,
        valor AS descricao_grau_instrucao
    FROM `basedosdados.br_me_caged.dicionario`
    WHERE
        TRUE
        AND nome_coluna = 'grau_instrucao'
        AND id_tabela = 'microdados_movimentacao'
),
dicionario_tipo_estabelecimento AS (
    SELECT
        chave AS chave_tipo_estabelecimento,
        valor AS descricao_tipo_estabelecimento
    FROM `basedosdados.br_me_caged.dicionario`
    WHERE
        TRUE
        AND nome_coluna = 'tipo_estabelecimento'
        AND id_tabela = 'microdados_movimentacao'
),
dicionario_tipo_movimentacao AS (
    SELECT
        chave AS chave_tipo_movimentacao,
        valor AS descricao_tipo_movimentacao
    FROM `basedosdados.br_me_caged.dicionario`
    WHERE
        TRUE
        AND nome_coluna = 'tipo_movimentacao'
        AND id_tabela = 'microdados_movimentacao'
),
aggregated_data AS (
    SELECT
        dados.ano as ano,
        dados.mes as mes,
        dados.sigla_uf AS sigla_uf,
        SUM(dados.saldo_movimentacao) as saldo_movimentacao,
        dados.cbo_2002 AS cbo_2002,
        dados.categoria AS categoria,
        dados.grau_instrucao AS grau_instrucao,
        dados.tipo_estabelecimento AS tipo_estabelecimento,
        dados.tipo_movimentacao AS tipo_movimentacao
    FROM `basedosdados.br_me_caged.microdados_movimentacao` AS dados
    WHERE (dados.ano = 2023 AND dados.mes >= 8)
       OR (dados.ano = 2024 AND dados.mes <= 7)
    GROUP BY
        dados.ano,
        dados.mes,
        dados.sigla_uf,
        dados.cbo_2002,
        dados.categoria,
        dados.grau_instrucao,
        dados.tipo_estabelecimento,
        dados.tipo_movimentacao
)
SELECT
    aggregated_data.ano,
    aggregated_data.mes,
    aggregated_data.sigla_uf,
    diretorio_sigla_uf.nome AS sigla_uf_nome,
    aggregated_data.saldo_movimentacao,
    aggregated_data.cbo_2002,
    diretorio_cbo_2002.descricao AS cbo_2002_descricao,
    diretorio_cbo_2002.descricao_familia AS cbo_2002_descricao_familia,
    diretorio_cbo_2002.descricao_subgrupo AS cbo_2002_descricao_subgrupo,
    diretorio_cbo_2002.descricao_subgrupo_principal AS cbo_2002_descricao_subgrupo_principal,
    diretorio_cbo_2002.descricao_grande_grupo AS cbo_2002_descricao_grande_grupo,
    descricao_categoria AS categoria,
    descricao_grau_instrucao AS grau_instrucao,
    descricao_tipo_estabelecimento AS tipo_estabelecimento,
    descricao_tipo_movimentacao AS tipo_movimentacao
FROM aggregated_data
LEFT JOIN (SELECT DISTINCT sigla, nome FROM `basedosdados.br_bd_diretorios_brasil.uf`) AS diretorio_sigla_uf
    ON aggregated_data.sigla_uf = diretorio_sigla_uf.sigla
LEFT JOIN (SELECT DISTINCT cbo_2002, descricao, descricao_familia, descricao_subgrupo, descricao_subgrupo_principal, descricao_grande_grupo
           FROM `basedosdados.br_bd_diretorios_brasil.cbo_2002`) AS diretorio_cbo_2002
    ON aggregated_data.cbo_2002 = diretorio_cbo_2002.cbo_2002
LEFT JOIN `dicionario_categoria`
    ON aggregated_data.categoria = chave_categoria
LEFT JOIN `dicionario_grau_instrucao`
    ON aggregated_data.grau_instrucao = chave_grau_instrucao
LEFT JOIN `dicionario_tipo_estabelecimento`
    ON aggregated_data.tipo_estabelecimento = chave_tipo_estabelecimento
LEFT JOIN `dicionario_tipo_movimentacao`
    ON aggregated_data.tipo_movimentacao = chave_tipo_movimentacao
LIMIT 1000;
