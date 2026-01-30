import re
from leitor_cod_barras import extrair_codigo_barras_ocr



# IDENTIFICAÇÃO DO CÓDIGO IRPJ
def identificar_codigo_irpj(texto):
    """
    Retorna:
    - 2089 - IRPJ Lucro Presumido
    - 2362 - IRPJ Mensal - Lucro Real Obrigatório
    - 0220 - IRPJ Trimestral - Lucro Real Obrigatório
    - 5993 - IRPJ Mensal - Lucro Real Opcional
    - 3373 - IRPJ Trimestral - Lucro Real Opcional
    """
    texto = texto.upper()

    codigos_irpj = {
        "2089": "Lucro Presumido",
        "2362": "Mensal – Lucro Real Obrigatório",
        "0220": "Trimestral – Lucro Real Obrigatório",
        "5993": "Mensal – Lucro Real Opcional",
        "3373": "Trimestral – Lucro Real Opcional",
    }

    padrao = r"(CÓDIGO DE RECEITA|CÓDIGO)?\s*[:\-]?\s*(2089|2362|0220|5993|3373)"
    match = re.search(padrao, texto)

    if not match:
        return None

    codigo = match.group(2)
    tipo = codigos_irpj.get(codigo)

    return {
        "codigo": codigo,
        "descricao": tipo
    }



# VALIDAÇÃO IRPJ (EXCLUSIVA)
def validar(texto):
    texto = texto.upper()

    evidencias_irpj = [
        "IRPJ",
        "IMPOSTO DE RENDA DA PESSOA JURÍDICA",
    ]

    evidencias_receita = [
        "DOCUMENTO DE ARRECADAÇÃO",
        "DARF",
        "RECEITA FEDERAL",
        "RFB",
    ]

    impostos_proibidos = [
        "PIS",
        "COFINS",
        "CSLL",
        "INSS",
        "ICMS",
        "ISS",
        "IPTU",
        "ITBI",
    ]

    tem_irpj = any(p in texto for p in evidencias_irpj)
    tem_receita = any(p in texto for p in evidencias_receita)
    tem_proibido = any(p in texto for p in impostos_proibidos)
    tem_codigo = identificar_codigo_irpj(texto) is not None

    return tem_irpj and tem_receita and tem_codigo and not tem_proibido


# Extrair Razão social
def extrair_razao_social(texto):
    linhas = texto.splitlines()

    for i, linha in enumerate(linhas):
        if "RAZÃO SOCIAL" in linha.upper() and i + 1 < len(linhas):
            razao = linhas[i + 1].strip()

            razao = re.sub(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", "", razao)
            razao = re.sub(
                r"\b(DARF|RECEITA FEDERAL|RFB|IRPJ|CSLL)\b.*",
                "",
                razao,
                flags=re.IGNORECASE
            )

            return re.sub(r"\s{2,}", " ", razao).strip()

    return None



# Extrair CNPJ
def extrair_cnpj(texto):
    match = re.search(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", texto)
    return match.group() if match else None



# Extrair vencimento
def extrair_vencimento(texto):
    match = re.search(
        r"PAGAR ATÉ[:\s]+(\d{2}/\d{2}/\d{4})|VENCIMENTO[:\s]+(\d{2}/\d{2}/\d{4})",
        texto,
        re.IGNORECASE
    )
    return match.group(1) or match.group(2) if match else None



# Extrair Apuração
def extrair_apuracao(texto):
    texto = texto.upper()

    meses = {
        "JANEIRO": "01",
        "FEVEREIRO": "02",
        "MARÇO": "03",
        "MARCO": "03",
        "ABRIL": "04",
        "MAIO": "05",
        "JUNHO": "06",
        "JULHO": "07",
        "AGOSTO": "08",
        "SETEMBRO": "09",
        "OUTUBRO": "10",
        "NOVEMBRO": "11",
        "DEZEMBRO": "12",
    }

    # 1 Identificar Período de Apuração
    match = re.search(r"\bPeríodo de Apuração\s*(\d{2}/\d{4})", texto)
    if match:
        return match.group(1)

    # 2 MM/AAAA direto
    match = re.search(r"\b(0[1-9]|1[0-2])/\d{4}\b", texto)
    if match:
        return match.group(0)

    # 3 Janeiro/2026 ou Janeiro 2026
    match = re.search(
        r"\b(JANEIRO|FEVEREIRO|MARÇO|MARCO|ABRIL|MAIO|JUNHO|JULHO|AGOSTO|SETEMBRO|OUTUBRO|NOVEMBRO|DEZEMBRO)[\s/]+(\d{4})",
        texto
    )
    if match:
        mes_nome, ano = match.groups()
        mes_num = meses.get(mes_nome)
        return f"{mes_num}/{ano}"

    return None




# Extrair número do documento
def extrair_numero_documento(texto):
    padrao = r"Número:\s*([\s\S]*?)(\d[\d\.\-]+)"
    match = re.search(padrao, texto)
    return match.group(2) if match else None




# Extrair Valor do documento
def extrair_valor_documento(texto):
    texto = texto.replace("\n", " ")
    match = re.search(
        r"(VALOR TOTAL DO DOCUMENTO|VALOR)[^\d]{0,20}"
        r"(\d{1,3}(?:\.\d{3})*,\d{2})",
        texto,
        re.IGNORECASE
    )
    return f"R$ {match.group(2)}" if match else None




# CÓDIGO DE BARRAS
def calcular_dv_boleto(codigo_43):
    pesos = [2, 3, 4, 5, 6, 7, 8, 9]
    soma = 0
    idx = 0

    for digito in reversed(codigo_43):
        soma += int(digito) * pesos[idx]
        idx = (idx + 1) % len(pesos)

    resto = soma % 11
    dv = 11 - resto
    return "1" if dv in (0, 10, 11) else str(dv)


def extrair_codigo_barras(texto, caminho_pdf):
    candidatos = re.findall(r"\d{20,}", texto)
    codigo = max(candidatos, key=len) if candidatos else None

    if not codigo:
        codigo = extrair_codigo_barras_ocr(caminho_pdf)

    if not codigo:
        return None

    codigo = re.sub(r"\D", "", codigo)

    if len(codigo) == 44:
        return codigo

    if len(codigo) == 43:
        return codigo + calcular_dv_boleto(codigo)

    if len(codigo) > 44:
        base = codigo[:43]
        return base + calcular_dv_boleto(base)

    return None



# EXTRAÇÃO FINAL (Json)
def extrair(texto, caminho_pdf):
    codigo_info = identificar_codigo_irpj(texto)

    return {
        "esfera": "FEDERAL",
        "codigo": codigo_info.get("codigo") if codigo_info else None,
        "descricao": codigo_info.get("descricao") if codigo_info else None,
        "razao_social": extrair_razao_social(texto),
        "cnpj": extrair_cnpj(texto),
        "documento": extrair_numero_documento(texto),
        "competencia": extrair_apuracao(texto),
        "vencimento": extrair_vencimento(texto),
        "valor": extrair_valor_documento(texto),
        "codigo_barras": extrair_codigo_barras(texto, caminho_pdf),
    }

