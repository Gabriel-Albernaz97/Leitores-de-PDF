import re


# VALIDAÇÃO ICMS
def validar(texto):
    texto = texto.upper()

    evidencias = [
        "APURAÇÃO DO ICMS",
        "SPED FISCAL",
        "EFD ICMS",
    ]

    bloqueios = [
        "IRPJ", "CSLL", "PIS", "COFINS",
        "ECD", "ECF", "CONTRIBUIÇÕES",
    ]

    return any(e in texto for e in evidencias) and not any(b in texto for b in bloqueios)



# IDENTIFICAÇÃO DA ESCRITURAÇÃO
def extrair_identificacao_escrituracao(texto):
    def b(p):
        return _buscar_linha(texto, p)

    periodo = b(r"Período:\s*(\d{2}/\d{2}/\d{4})\s*a\s*(\d{2}/\d{2}/\d{4})")

    return {
        "contribuinte": b(r"Contribuinte:\s*(.+)"),
        "cnpj_contribuinte": b(r"CNPJ/CPF:\s*([\d\./\-]+)"),
        "inscricao_estadual": b(r"Inscrição Estadual:\s*([\w\d]+)"),
        "uf": b(r"UF:\s*([A-Z]{2})"),
        "perfil": b(r"Perfil:\s*([A-Z])"),
        "periodo_inicio": periodo[0] if periodo else None,
        "periodo_fim": periodo[1] if periodo else None,
        "competencia": periodo[1][3:] if periodo else None,
        "hash_arquivo": b(r"Hash do Arquivo:\s*([A-F0-9]+)")
    }



# DIFAL + FCP (POR UF)
def extrair_difal_fcp(texto):
    bloco = re.search(
        r"APURAÇÃO DO ICMS\s*-\s*DIFERENCIAL\s+DE\s+AL[ÍI]QUOTA\s+E\s+FCP([\s\S]+?)"
        r"(APURAÇÃO DO ICMS|APURAÇÃO DO IPI|APURAÇÃO DO ISS|ESCRITURAÇÃO RECEBIDA|$)",
        texto,
        re.IGNORECASE
    )

    if not bloco:
        return None

    linhas = [
        l.strip()
        for l in bloco.group(1).splitlines()
        if l.strip() and not re.search(r"^Página \d+ de \d+", l, re.I)
    ]

    resultados = []
    uf = periodo = None
    impostos = {}

    for linha in linhas:
        m_uf_periodo = re.search(
            r"^([A-Z]{2})\s+(\d{2}/\d{2}/\d{4}\s*a\s*\d{2}/\d{2}/\d{4})",
            linha
        )
        if m_uf_periodo:
            uf, periodo = m_uf_periodo.groups()
            continue

        m_imp = re.search(
            r"^(DIFAL|FCP)\s+R\$\s*([\d\.,]+)\s+R\$\s*([\d\.,]+)\s+R\$\s*([\d\.,]+)",
            linha,
            re.I
        )
        if m_imp:
            impostos[m_imp.group(1).upper()] = {
                "saldo_credor": f"R$ {m_imp.group(2)}",
                "valor_recolher": f"R$ {m_imp.group(3)}",
                "extra_apuracao": f"R$ {m_imp.group(4)}",
            }

        if uf and periodo and "DIFAL" in impostos and "FCP" in impostos:
            resultados.append({
                "uf": uf,
                "periodo": periodo,
                "impostos": impostos
            })
            uf = periodo = None
            impostos = {}

    return resultados if resultados else None



# ICMS ST – SUBSTITUIÇÃO TRIBUTÁRIA (OBJETO SIMPLES)
def extrair_icms_st(texto):
    bloco = re.search(
        r"APURAÇÃO DO ICMS\s*-\s*SUBSTITUIÇÃO\s+TRIBUTÁRIA([\s\S]+?)"
        r"(APURAÇÃO DO ICMS\s*-|APURAÇÃO DO IPI|APURAÇÃO DO ISS|ESCRITURAÇÃO RECEBIDA|$)",
        texto,
        re.IGNORECASE
    )

    if not bloco:
        return None

    linhas = [
        l.strip()
        for l in bloco.group(1).splitlines()
        if l.strip() and not re.search(r"Página \d+ de \d+", l, re.I)
    ]

    resultados = []

    for linha in linhas:
        if not re.match(r"^[A-Z]{2}\b", linha):
            continue

        uf = re.match(r"^([A-Z]{2})\b", linha).group(1)

        periodo = None
        p = re.search(r"\d{2}/\d{2}/\d{4}\s*a\s*\d{2}/\d{2}/\d{4}", linha)
        if p:
            periodo = p.group()

        valores = re.findall(r"R\$\s*[\d\.,]+", linha)

        if len(valores) < 3:
            continue

        resultados.append({
            "uf": uf,
            "periodo": periodo,
            "saldo_credor_st": valores[0],
            "icms_st_recolher": valores[1],
            "extra_apuracao": valores[2]
        })

    return resultados if resultados else None



# QUADROS GENÉRICOS (ICMS PRÓPRIO, IPI, ISS)
def extrair_quadros_genericos(texto):
    quadros = {}

    padrao = re.compile(r"(APURAÇÃO DO [A-Z\s\-]+)", re.I)
    partes = padrao.split(texto)

    for i in range(1, len(partes), 2):
        titulo = partes[i].strip()
        # NORMALIZA TÍTULOS QUE VÊM COM OCR SUJO (ex: "\nPer")
        titulo = re.sub(r"\s+PER.*$", "", titulo, flags=re.I).strip()
        TITULOS_CANONICOS = {
        "APURAÇÃO DO ICMS - OPERA": "APURAÇÃO DO ICMS - OPERAÇÕES PRÓPRIAS",
        "APURAÇÃO DO ICMS - OPERAÇÕES": "APURAÇÃO DO ICMS - OPERAÇÕES PRÓPRIAS",
        }
        titulo = partes[i].strip()
        # Remove lixo tipo "\nPer"
        titulo = re.sub(r"\s+PER.*$", "", titulo, flags=re.I).strip()
        # NORMALIZA TÍTULOS CONHECIDOS
        titulo = TITULOS_CANONICOS.get(titulo.upper(), titulo)
        titulo_upper = titulo.upper()
        conteudo = partes[i + 1]

        # BLOQUEIO TOTAL DE DIFAL E ST
        if any(x in titulo_upper for x in ["DIFERENCIAL", "FCP", "SUBSTITUI"]):
            continue

        itens = []
        for linha in conteudo.splitlines():
            m = re.search(r"(.+?)\s*R\$\s*([\d\.,]+)", linha)
            if m:
                itens.append({
                    "descricao": m.group(1).strip(),
                    "valor": f"R$ {m.group(2)}"
                })

        if itens:
            quadros[titulo] = {"itens": itens}

    return quadros if quadros else None



# TRANSMISSÃO SPED
def extrair_transmissao_sped(texto):
    texto_upper = texto.upper()
    dados = {}




    # CPF (único no documento)
    cpf = re.search(r"\d{3}\.\d{3}\.\d{3}-\d{2}", texto)
    if cpf:
        dados["cpf_responsavel"] = cpf.group()





    # CNPJ PRESTADOR = último CNPJ do documento
    cnpjs = re.findall(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", texto)
    if cnpjs:
        dados["cnpj_prestador"] = cnpjs[-1]





    # Data e hora de recebimento
    dt = re.search(
        r"RECEBIDA VIA INTERNET.*?(\d{2}/\d{2}/\d{4}).*?(\d{2}:\d{2}:\d{2})",
        texto_upper,
        re.DOTALL
    )
    if dt:
        dados["data_hora_recebimento"] = f"{dt.group(1)} {dt.group(2)}"




    # Agente receptor
    if "SERPRO" in texto_upper:
        dados["agente_receptor"] = "SERPRO"




    # BLOCO SEMÂNTICO DOS HASHES (RECIBO + ASSINATURA)
    bloco_match = re.search(
        r"ESCRITURAÇÃO RECEBIDA VIA INTERNET([\s\S]+)",
        texto_upper
    )

    if not bloco_match:
        return dados if dados else None

    bloco = bloco_match.group(1)

    # Normaliza OCR: remove linhas vazias e lineariza
    texto_linear = " ".join(
        linha.strip()
        for linha in bloco.splitlines()
        if linha.strip()
    )

    # Captura todos os hashes possíveis
    hashes = re.findall(
        r"[A-F0-9]{2}(?:\.[A-F0-9]{2}){5,}-?\d?",
        texto_linear
    )

    if not hashes:
        return dados if dados else None




    # REGRA SEMÂNTICA DO SPED
    idx_fim_recibo = None
    for i, h in enumerate(hashes):
        if re.search(r"-\d$", h):
            idx_fim_recibo = i
            break

    if idx_fim_recibo is None:
        return dados if dados else None

    recibo_inicio = hashes[0]
    recibo_fim = hashes[idx_fim_recibo]

    assinatura_partes = hashes[1:idx_fim_recibo]

    dados["numero_recibo"] = f"{recibo_inicio} {recibo_fim}"

    if assinatura_partes:
        dados["assinatura_transmissao"] = " ".join(assinatura_partes)

    return dados if dados else None




# AUXILIAR
def _buscar_linha(texto, padrao):
    m = re.search(padrao, texto, re.I)
    if not m:
        return None
    return m.group(1).strip() if len(m.groups()) == 1 else tuple(g.strip() for g in m.groups())



# EXTRAÇÃO FINAL
def extrair(texto, caminho_pdf=None):
    dados_impostos = {}



    genericos = extrair_quadros_genericos(texto)
    if genericos:
        dados_impostos.update(genericos)
        
    st = extrair_icms_st(texto)
    if st:
        dados_impostos["APURAÇÃO DO ICMS - SUBSTITUIÇÃO TRIBUTÁRIA"] = st

    difal = extrair_difal_fcp(texto)
    if difal:
        dados_impostos["APURAÇÃO DO ICMS - DIFERENCIAL DE ALÍQUOTA E FCP"] = difal


    return {
        "esfera": "ESTADUAL",
        "escrituracao": extrair_identificacao_escrituracao(texto),
        "dados_impostos": dados_impostos,
        "transmissao": extrair_transmissao_sped(texto),
    }
