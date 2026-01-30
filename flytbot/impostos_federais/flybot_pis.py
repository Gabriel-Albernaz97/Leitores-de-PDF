import re
from leitor_cod_barras import extrair_codigo_barras_ocr



# VALIDAÇÃO (EXCLUSIVA PIS)
def validar(texto):
    texto = texto.upper()

    evidencias_receita = [
        "RECEITA FEDERAL",
        "RFB",
        "DARF",
    ]

    evidencias_pis = [
        "PIS",
        "PROGRAMA DE INTEGRAÇÃO SOCIAL",
    ]

    impostos_proibidos = [
        "COFINS",
        "CSLL",
        "IRPJ",
        "IPI",
    ]

    tem_receita = any(p in texto for p in evidencias_receita)
    tem_pis = any(p in texto for p in evidencias_pis)
    tem_proibido = any(p in texto for p in impostos_proibidos)

    codigo, tipo = identificar_codigo_pis(texto)
    tem_codigo = codigo is not None

    return tem_receita and tem_pis and tem_codigo and not tem_proibido



# IDENTIFICAÇÃO DO CÓDIGO PIS
def identificar_codigo_pis(texto):
    """
    Códigos PIS:
    - 8109 – Lucro Presumido
    - 6912 – Lucro Real
    """
    texto = texto.upper()

    codigos_pis = {
        "8109": "Lucro Presumido",
        "6912": "Lucro Real",
    }

    padrao = r"(CÓDIGO DE RECEITA|CÓDIGO)?\s*[:\-]?\s*(8109|6912)"
    match = re.search(padrao, texto)

    if not match:
        return None, None

    codigo = match.group(2)
    tipo = codigos_pis.get(codigo)

    return codigo, tipo



# Extrair Razão social
def extrair_razao_social(texto):
    linhas = texto.splitlines()

    for i, linha in enumerate(linhas):
        if "RAZÃO SOCIAL" in linha.upper() and i + 1 < len(linhas):
            razao = linhas[i + 1]
            razao = re.sub(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", "", razao)
            razao = re.sub(r"\b(PIS|COFINS|DARF|RFB)\b.*", "", razao, flags=re.I)
            return re.sub(r"\s{2,}", " ", razao).strip()

    return None



# Extrair CNPJ
def extrair_cnpj(texto):
    match = re.search(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", texto)
    return match.group() if match else None



# Extrair Número do Documento
def extrair_numero_documento(texto):
    padrao = r"Número:\s*([\s\S]*?)(\d[\d\.\-]+)"
    match = re.search(padrao, texto)
    return match.group(2) if match else None



# Extrair Venciemnto
def extrair_vencimento(texto):
    match = re.search(
        r"PAGAR ATÉ[:\s]+(\d{2}/\d{2}/\d{4})|VENCIMENTO[:\s]+(\d{2}/\d{2}/\d{4})",
        texto,
        re.I
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


# Extrair valor do documento
def extrair_valor_documento(texto):
    texto = texto.replace("\n", " ")
    match = re.search(
        r"(VALOR TOTAL DO DOCUMENTO|VALOR)[^\d]{0,20}"
        r"(\d{1,3}(?:\.\d{3})*,\d{2})",
        texto,
        re.I
    )
    return f"R$ {match.group(2)}" if match else None



# CÓDIGO DE BARRAS
def extrair_codigo_barras(texto, caminho_pdf):
    candidatos = re.findall(r"\d{20,}", texto)
    codigo = max(candidatos, key=len) if candidatos else None

    if not codigo:
        codigo = extrair_codigo_barras_ocr(caminho_pdf)

    return codigo




# EXTRAÇÃO FINAL (CONTRATO OFICIAL)
def extrair(texto, caminho_pdf):
    codigo, tipo = identificar_codigo_pis(texto)

    return {
        "esfera": "FEDERAL",
        "codigo": codigo,
        "descricao": tipo,
        "razao_social": extrair_razao_social(texto),
        "cnpj": extrair_cnpj(texto),
        "documento": extrair_numero_documento(texto),
        "competencia": extrair_apuracao(texto),
        "vencimento": extrair_vencimento(texto),
        "valor": extrair_valor_documento(texto),
        "codigo_barras": extrair_codigo_barras(texto, caminho_pdf),
    }
