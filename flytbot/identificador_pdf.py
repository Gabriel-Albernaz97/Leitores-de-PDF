import pdfplumber
import json
import sys
import os

# Impostos Federais
from impostos_federais.flybot_pis import validar as validar_pis, extrair as extrair_pis
from impostos_federais.flybot_ipi import validar as validar_ipi, extrair as extrair_ipi
from impostos_federais.flybot_cofins import validar as validar_cofins, extrair as extrair_cofins
from impostos_federais.flybot_irpj import validar as validar_irpj, extrair as extrair_irpj
from impostos_federais.flybot_csll import validar as validar_csll, extrair as extrair_csll


# Impostos Estaduais
from impostos_estaduais.flybot_icms import validar as validar_icms, extrair as extrair_icms




# Impostos Municipais




def extrair_texto_pdf(caminho_pdf):
    texto = ""
    with pdfplumber.open(caminho_pdf) as pdf:
        for page in pdf.pages:
            conteudo = page.extract_text()
            if conteudo:
                texto += conteudo + "\n"
    return texto



# CONTADOR RECURSIVO DE CAMPOS VÁLIDOS
def contar_campos_validos(dados):
    if dados is None:
        return 0

    if isinstance(dados, dict):
        return sum(contar_campos_validos(v) for v in dados.values())

    if isinstance(dados, list):
        return sum(contar_campos_validos(v) for v in dados)

    if isinstance(dados, str):
        return 1 if dados.strip() else 0

    return 1



# IDENTIFICADOR MESTRE
def identificar_pdf(caminho_pdf):
    texto = extrair_texto_pdf(caminho_pdf)

    leitores = [
        ("PIS", validar_pis, extrair_pis),
        ("IPI", validar_ipi, extrair_ipi),
        ("COFINS", validar_cofins, extrair_cofins),
        ("IRPJ", validar_irpj, extrair_irpj),
        ("CSLL", validar_csll, extrair_csll),
        ("ICMS", validar_icms, extrair_icms),
    ]

    MIN_CAMPOS_VALIDOS = 5

    for nome, validar, extrair in leitores:
        try:
            # 1 Validação semântica
            if not validar(texto):
                continue

            # 2 Extração estruturada
            dados = extrair(texto, caminho_pdf)

            # 3 Confirmação por densidade de dados
            total_campos = contar_campos_validos(dados)

            if total_campos >= MIN_CAMPOS_VALIDOS:
                return {
                    "status": "true",
                    "identificado": nome,
                    "campos_validos": total_campos,
                    "dados": dados
                }

        except Exception:
            continue

    return {
        "status": "false",
        "mensagem": "Nenhum imposto identificado com dados suficientes"
    }



# EXECUÇÃO VIA CLI
if __name__ == "__main__":

    # 1 Caminho não informado
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "false",
            "mensagem": "Caminho do PDF não informado"
        }, ensure_ascii=False, indent=2))
        sys.exit(1)

    caminho_pdf = sys.argv[1]

    # 2 Arquivo inexistente
    if not os.path.isfile(caminho_pdf):
        print(json.dumps({
            "status": "false",
            "mensagem": "Arquivo PDF não encontrado",
            "caminho": caminho_pdf
        }, ensure_ascii=False, indent=2))
        sys.exit(1)

    # 3 Identificação
    resultado = identificar_pdf(caminho_pdf)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))