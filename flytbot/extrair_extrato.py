import pdfplumber
import pandas as pd
import re


caminho_pdf = "/home/gabriel/Downloads/Extrato Mensal.pdf"
# caminho_pdf = "/home/carlos/Downloads/extrato_folha.pdf"
data = []


# Ler o PDF e extrair o texto
def extrair_texto_pdf(caminho_pdf):
    texto = ""
    with pdfplumber.open(caminho_pdf) as pdf:
        for page in pdf.pages:
            conteudo = page.extract_text()
            if conteudo:
                texto += conteudo + "\n"
    return texto



    # Extrair quadros do texto
def buscar(padrao, texto):
    match = re.search(padrao, texto)
    return match.group(1).strip() if match else None



    # Regularizar valores numéricos
def regularizar(regularizar):
    if regularizar is None:
        return None
    regularizar = str(regularizar).strip()

    # hh:mm -> horas decimais
    match = re.match(r"^(\d+):(\d+)$", regularizar)
    if match:
        h = int(match.group(1)); mm = int(match.group(2))
        return h + mm/60.0

    
    # remove caracteres e mantém dígitos, pontos, vírgulas e sinal
    regularizar_arrumar = re.sub(r"[^\d\.,\-]", "", regularizar)
    if regularizar_arrumar == "":
        return None
    regularizar_arrumar = regularizar_arrumar.replace(".", "").replace(",", ".")
    try:
        return float(regularizar_arrumar)
    except Exception:
        return None



    # Extrair informações da Empresa
def extrair_empresa(texto):
    dados = {}
    dados["Empresa_Nome"] = buscar(r"Empresa\:\s*(?:\d+\s*[-–—]\s*)?(.+?)(?:\s*Página\:|\s*$)", texto)
    dados["CNPJ"] = buscar(r"CNPJ\:\s*([\d\.\-\/]+)", texto)
    dados["Emissao"] = buscar(r"Emissão\:\s*([\d\/]+)", texto)
    dados["Calculo"] = buscar(r"Cálculo\:\s*(.+)", texto)
    dados["Horas"] = buscar(r"Horas\:\s*([\d\,]+)", texto)
    dados["Competencia"] = buscar(r"Competência\:\s*([\d\/]+)", texto)

    return dados



    # Extrair cabeçalho do texto
def extrair_cabecalho(texto):
    dados = {}

    dados["Cod_Funcionario"] = buscar(r"Empr\.\:\s*(\d+)", texto)
    nome = None
    match = re.search(r"Empr\.\:\s*(?:\d+)?\s*([A-Za-zÀ-ÿ][^\n\r]*?)\s*(?=Situação\:|CPF\:|Adm\:|Vínculo\:|$)", texto)
    if match: nome = match.group(1).strip()
    dados["Funcionario"] = nome
    dados["Situacao"] = buscar(r"Situação\:\s*(\w+)", texto)
    dados["CPF"] = buscar(r"CPF\:\s*([\d\.\-]+)", texto)
    dados["Admissao"] = buscar(r"Adm\:\s*([\d\/]+)", texto)
    dados["Vinculo"] = buscar(r"Vínculo\:\s*(\w+)", texto)
    dados["CC"] = buscar(r"CC\:\s*(\d+)", texto)
    dados["Departamento"] = buscar(r"Depto\:\s*(\d+)", texto)
    dados["Horas_Mes"] = buscar(r"Horas Mês\:\s*([\d\,]+)", texto)
    dados["Cod_Cargo"] = buscar(r"Cargo\:\s*(\d+)", texto)
    dados["Cargo"] = buscar(r"Cargo\:\s*\d*\s*([^\n\r]+?)(?=\s*C\.B\.O\:|\s*Filial\:|$)", texto)
    dados["CBO"] = buscar(r"C\.B\.O\:\s*(\d+)", texto)
    dados["Filial"] = buscar(r"Filial\:\s*(\d+)", texto)
    dados["Salario"] = buscar(r"Salário\:\s*([\d\.,]+)", texto)


    for d in ["Horas_Mes", "Salario"]:
        if dados[d]:
            dados[d] = float(dados[d].replace(".", "").replace(",", "."))

    return dados



# Extrair detalhamento do texto
def extrair_detalhamento(texto):
    linhas = texto.splitlines()
    eventos = []

    # captura múltiplos eventos por linha
    padrao = re.compile(r"(\d{2,5})\s*([A-Za-zÀ-ÿ0-9\.,\-/\s%°ºª]+?)\s+((?:\d+:\d+)|(?:[\d.,]+))\s+([\d.,]+)\s*([PD])", re.I)

    funcionario_atual = False

    for linha in linhas:
        if "Empr.:" in linha:
            funcionario_atual = True
            continue

        if funcionario_atual and "Base IRRF:" in linha:
            funcionario_atual = False
            continue

        if not funcionario_atual:
            continue

        # procurar múltiplos eventos dentro da mesma linha
        for match in padrao.finditer(linha):
            codigo = match.group(1)
            descricao = match.group(2).strip()
            quantidade = match.group(3)
            valor_evento = match.group(4)
            tipo = "Provento" if match.group(5).upper() == "P" else "Desconto"

            eventos.append({
                "Evento_codigo": codigo,
                "Descricao_Eventos": descricao,
                "Quantidade": regularizar(quantidade),
                "Valor_Evento": regularizar(valor_evento),
                "Tipo_Evento": tipo
            })

    eventos.sort(key=lambda x: 0 if x["Tipo_Evento"] == "Provento" else 1)
    return eventos




# Extrair final do texto
def extrair_final(texto):
    dados = {}

    dados["ND"] = buscar(r"ND\:\s*(\d+)", texto)
    dados["NF"] = buscar(r"NF\:\s*(\d+)", texto)
    dados["Proventos"] = buscar(r"Proventos\:\s*([\d\.,]+)", texto)
    dados["Base_INSS"] = buscar(r"Base INSS\:\s*([\d\.,]+)", texto)
    dados["Descontos"] = buscar(r"Descontos\:\s*([\d\.,]+)", texto)
    dados["Excedente_INSS"] = buscar(r"Excedente INSS\:\s*([\d\.,]+)", texto)
    dados["Informativa"] = buscar(r"Informativa\:\s*([\d\.,]+)", texto)
    dados["Base_FGTS"] = buscar(r"Base FGTS\:\s*([\d\.,]+)", texto)
    dados["Informativa_Dedutora"] = buscar(r"Informativa Dedutora\:\s*(\d+)", texto)
    dados["Valor_FGTS"] = buscar(r"Valor FGTS\:\s*([\d\.,]+)", texto)
    dados["Liquido"] = buscar(r"Líquido\:\s*([\d\.,]+)", texto)
    dados["Base_IRRF"] = buscar(r"Base IRRF\:\s*([\d\.,]+)", texto)

    for d in ["Proventos", "Base_INSS", "Descontos", "Excedente_INSS", "Informativa", "Base_FGTS", "Valor_FGTS", "Liquido", "Base_IRRF"]:
        if dados.get(d):
            valor = dados[d]
            valor = valor.replace(".", "").replace(",", ".")
            dados[d] = float(valor)


    return dados




# extrair todo o texto do PDF
texto = extrair_texto_pdf(caminho_pdf)

linhas = texto.splitlines()

cabecalho_arquivo = extrair_empresa(texto)
empregados = []
cabecalho_empregado = {}
eventos = []
detalhe_evento = {}
rodape_empregado = {}

indice_linha = 0
linhas_empregado = []
empregado = {}
for linha in linhas:
    if indice_linha < 5:
        indice_linha += 1
        continue

    # colaboradores
    if "Empr.:" in linha:
        if linhas_empregado:
            empregados.append(linhas_empregado)
            linhas_empregado = []
    linhas_empregado.append(linha)


if linhas_empregado:
    empregados.append(linhas_empregado)

#print(f"Total de empregados: {len(empregados)}")


dados_empregados = []
dados_empregado = {}
for empregado in empregados:
    texto_empregado = "\n".join(empregado)
    cabecalho = extrair_cabecalho(texto_empregado)
    eventos = extrair_detalhamento(texto_empregado)
    rodape = extrair_final(texto_empregado)
    if eventos == None:
        continue
    for evento in eventos:
        dados_empregado = {**cabecalho, **rodape, **evento}
        dados_empregados.append(dados_empregado)


df = pd.DataFrame(dados_empregados)
df.to_csv("extrato_mensal.csv", index=False)