# Sistema de Avaliação de Estudantes de Medicina

Sistema web para avaliação processual de estudantes de medicina em unidades básicas de saúde.

## Funcionalidades

- Dashboard com visão geral dos grupos
- Sistema de avaliação nas 3 dimensões (Atitude, Habilidade, Cognição)
- Cálculo automático de médias
- Relatórios detalhados
- Interface responsiva (mobile-friendly)

## Tecnologias

- Python 3.11
- Flask
- SQLite
- HTML/CSS/JavaScript

## Deploy

Este projeto está configurado para deploy automático no Railway.app.

### Arquivos de configuração:
- `Procfile`: Comando de inicialização
- `railway.json`: Configurações do Railway
- `requirements.txt`: Dependências Python
- `runtime.txt`: Versão do Python

## Uso Local

1. Instalar dependências:
```bash
pip install -r requirements.txt
```

2. Executar aplicação:
```bash
python src/main.py
```

3. Acessar: http://localhost:5000

## Estrutura do Projeto

```
src/
├── main.py              # Aplicação principal
├── models/              # Modelos do banco de dados
├── routes/              # Rotas da API
├── static/              # Interface web
└── database/            # Banco de dados SQLite
```

## Importação de Dados

O sistema inclui funcionalidade para importar dados de planilhas Excel no formato específico da instituição.

## Suporte

Para dúvidas ou suporte, consulte a documentação completa fornecida junto com o sistema.

