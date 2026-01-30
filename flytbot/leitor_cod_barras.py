from pdf2image import convert_from_path
from pyzbar.pyzbar import decode, ZBarSymbol
import cv2
import numpy as np
import contextlib
import sys
import os


def extrair_codigo_barras_ocr(caminho_pdf):

    try:
        paginas = convert_from_path(caminho_pdf, dpi=300)
    except Exception:
        return None

    for pagina in paginas:
        imagem = np.array(pagina)

        # escala de cinza
        gray = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)

        # leve threshold melhora leitura
        gray = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )[1]

        # silencia warnings do zbar
        with _silenciar_stderr():
            codigos = decode(
                gray,
                symbols=[ZBarSymbol.I25, ZBarSymbol.CODE128]
            )

        for codigo in codigos:
            try:
                texto = codigo.data.decode("utf-8").strip()
            except Exception:
                continue

            # só números e tamanho mínimo seguro
            if texto.isdigit() and len(texto) >= 30:
                return texto

    return None


@contextlib.contextmanager
def _silenciar_stderr():
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(2)
    os.dup2(devnull, 2)

    try:
        yield
    finally:
        os.dup2(old_stderr, 2)
        os.close(devnull)
