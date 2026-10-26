# VENNA — Custos de Abertura

Sistema simples para registrar os custos de abertura da empresa.

## Como rodar (primeira vez)

1. Instale Python 3.11+ em https://www.python.org/downloads/ (marque "Add Python to PATH")
2. Abra a pasta no Explorador, clique na barra de endereço, digite `powershell` e Enter
3. Execute:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

O sistema abre em `http://localhost:8501`.

## Próximas vezes

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Dados

Os dados ficam em `venna_financeiro.db` nesta pasta. Não apague esse arquivo. Faça cópias de segurança regularmente.
