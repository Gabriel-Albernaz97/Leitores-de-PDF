import pdfplumber
import pandas as pd
import re

# caminho_pdf = "/home/gabriel/Downloads/Extrato Mensal.pdf"
caminho_pdf = "/home/carlos/Downloads/extrato_folha.pdf"
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


# Extrair informações da Empresa
def extrair_empresa(texto):
    dados = {}

    def buscar(padrao):
        match = re.search(padrao, texto)
        return match.group(1).strip() if match else None

    dados["Empresa_Nome"] = buscar(r"Empresa\:\-\s*(.+)")
    dados["CNPJ"] = buscar(r"CNPJ\:\s*([\d\.\-\/]+)")
    dados["Calculo"] = buscar(r"Cálculo\:\s*(.+)")
    dados["Competencia"] = buscar(r"Competência\:\s*([\d\/]+)")
    dados["Emissao"] = buscar(r"Emissão\:\s*([\d\/]+)")
    dados["Horas"] = buscar(r"Horas\:\s*([\d\,]+)")

    return dados


# Extrair cabeçalho do texto
def extrair_cabecalho(texto):
    dados = {}

    def buscar(padrao):
        match = re.search(padrao, texto)
        return match.group(1).strip() if match else None


    dados["Cod_Funcionario"] = buscar(r"Empr\.\:\s*(\d+)")
    dados["Funcionario"] = buscar(r"Empr\.\:\s*(\w+)")
    dados["Situacao"] = buscar(r"Situação\:\s*(\w+)")
    dados["CPF"] = buscar(r"CPF\:\s*([\d\.\-]+)")
    dados["Admissao"] = buscar(r"Adm\:\s*([\d\/]+)")
    dados["Vinculo"] = buscar(r"Vínculo\:\s*(\w+)")
    dados["CC"] = buscar(r"CC\:\s*(\d+)")
    dados["Departamento"] = buscar(r"Depto\:\s*(\d+)")
    dados["Horas_Mes"] = buscar(r"Horas Mês\:\s*([\d\,]+)")
    dados["Cod_Cargo"] = buscar(r"Cargo\:\s*(.+?)")
    dados["Cargo"] = buscar(r"Cargo\:\s*(\w+)")
    dados["CBO"] = buscar(r"C\.B\.O\:\s*(\d+)")
    dados["Filial"] = buscar(r"Filial\:\s*(\d+)")
    dados["Salario"] = buscar(r"Salário\:\s*([\d\.,]+)")


    for d in ["Horas_Mes", "Salario"]:
        if dados[d]:
            dados[d] = float(dados[d].replace(".", "").replace(",", "."))

    return dados


# ///////////////////////////////////////////////////////////////////////////////////////////////

# Extrair detalhamento do texto
def extrair_detalhamento(texto):
    linhas = texto.splitlines()
    eventos = []
    padrao = re.compile(
        r"^\s*(\d{3,5})\s+"
        r"(.+?)\s+"
        r"([\d.,]+)\s+"
        r"([\d.,]+)\s*"
        r"([PD])$"
    )

# Início do funcionário
    funcionario_atual = False

    for linha in linhas:
        if "Empr.:" in linha:
            funcionario_atual = True
            continue

        # Fim do funcionário
        if funcionario_atual and "Base IRRF:" in linha:
            funcionario_atual = False
            continue

        if not funcionario_atual:
            continue

        match = padrao.match(linha)
        if not match:
            continue

        tipo = "Provento" if match.group(5) == "P" else "Desconto"

        eventos.append({
            "Evento_codigo": match.group(1),
            "Descricao_Eventos": match.group(2).strip(),
            "Quantidade": match.group(3),
            "Valor_Evento": float(match.group(4).replace(".", "").replace(",", ".")),
            "Tipo_Evento": tipo
        })

    eventos.sort(key=lambda x: 0 if x["Tipo_Evento"] == "Provento" else 1)
    return eventos

# ///////////////////////////////////////////////////////////////////////////////////////////////

# Extrair final do texto
def extrair_final(texto):
    dados = {}

    def buscar(padrao):
        match = re.search(padrao, texto)
        return match.group(1).strip() if match else None

    dados["ND"] = buscar(r"ND\:\s*(\d+)")
    dados["NF"] = buscar(r"NF\:\s*(\d+)")
    dados["Proventos"] = buscar(r"Proventos\:\s*([\d\.,]+)")
    dados["Base_INSS"] = buscar(r"Base INSS\:\s*([\d\.,]+)")
    dados["Descontos"] = buscar(r"Descontos\:\s*([\d\.,]+)")
    dados["Excedente_INSS"] = buscar(r"Excedente INSS\:\s*([\d\.,]+)")
    dados["Informativa"] = buscar(r"Informativa\:\s*([\d\.,]+)")
    dados["Base_FGTS"] = buscar(r"Base FGTS\:\s*([\d\.,]+)")
    dados["Informativa_Dedutora"] = buscar(r"Informativa Dedutora\:\s*(\d+)")
    dados["Valor_FGTS"] = buscar(r"Valor FGTS\:\s*([\d\.,]+)")
    dados["Liquido"] = buscar(r"Líquido\:\s*([\d\.,]+)")
    dados["Base_IRRF"] = buscar(r"Base IRRF\:\s*([\d\.,]+)")

    for d in ["Proventos", "Base_INSS", "Descontos", "Excedente_INSS", "Informativa", "Base_FGTS", "Valor_FGTS", "Liquido", "Base_IRRF"]:
        if dados.get(d):
            valor = dados[d]
            valor = valor.replace(".", "").replace(",", ".")
            dados[d] = float(valor)


    return dados









texto = extrair_texto_pdf(caminho_pdf)



cabecalho = extrair_cabecalho(texto)
detalhamento = extrair_detalhamento(texto)
rodape = extrair_final(texto)




for evento in detalhamento:
    linha = {}
    linha.update(cabecalho)
    linha.update(evento)
    linha.update(rodape)
    data.append(linha)

df = pd.DataFrame(data)
df.to_csv("extrato_mensal.csv", index=False)