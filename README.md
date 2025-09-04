# CathPed - Sistema de Gestão de Pacientes 🩺

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.x-black?style=for-the-badge&logo=flask)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-336791?style=for-the-badge&logo=postgresql)
![Google Cloud](https://img.shields.io/badge/Google_Cloud-API-4285F4?style=for-the-badge&logo=google-cloud)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6-yellow?style=for-the-badge&logo=javascript)

**CathPed** é uma aplicação web full-stack, desenvolvida como uma solução completa e individual, para otimizar o fluxo de gerenciamento de pacientes na área médica. O sistema automatiza a entrada de dados via **Google Forms/Sheets** e organiza todo o ciclo de vida do paciente em uma interface web intuitiva e segura.

***

## 🎯 O Problema Resolvido

Na rotina médica, o encaminhamento de pacientes entre especialistas frequentemente resulta em dados descentralizados, planilhas manuais e dificuldade no acompanhamento do status de cada caso. Este processo manual é propenso a erros, consome tempo valioso e dificulta a visão geral do fluxo de trabalho.

O **CathPed** foi criado para resolver exatamente esse problema, oferecendo uma plataforma centralizada que automatiza a coleta de dados e estrutura o atendimento em etapas claras, desde a avaliação inicial até o acompanhamento pós-procedimento.

***

## ✨ Features Principais

-   ✅ **Sincronização Automática com Google Sheets**: Novos pacientes preenchidos em um Google Form são automaticamente importados para a aplicação, servindo como a única fonte de verdade para novas entradas.
-   ✅ **Fluxo de Trabalho Estruturado**: O sistema guia o usuário através de 4 etapas essenciais do atendimento: **Avaliação**, **Autorização**, **Execução do Procedimento** e **Acompanhamento Pós-Procedimento**. A interface se adapta dinamicamente, mostrando apenas a próxima ação necessária para cada paciente.
-   ✅ **Operações CRUD Completas**:
    -   **Create**: Novos pacientes são criados via API do Google Sheets.
    -   **Read**: Visualização e busca de pacientes em uma lista organizada.
    -   **Update**: O status do paciente é atualizado ao preencher os formulários de cada etapa.
    -   **Delete**: A exclusão de um paciente é sincronizada, removendo o registro tanto do banco de dados **PostgreSQL** quanto da planilha original no **Google Sheets**, garantindo a consistência dos dados.
-   ✅ **Autenticação Segura**: Acesso restrito à aplicação através de um sistema de login e sessão.
-   ✅ **Resumo do Paciente e Geração de PDF**: Uma visão consolidada de todas as informações do paciente, que pode ser exportada como um arquivo PDF diretamente do navegador, utilizando `jsPDF` e `html2canvas`.
-   ✅ **Busca e Filtragem**: Funcionalidade de busca para localizar pacientes rapidamente pelo nome.
-   ✅ **Interface Responsiva**: O design se adapta a diferentes tamanhos de tela, permitindo o uso em desktops e dispositivos móveis.

***

## 🏛️ Arquitetura e Fluxo de Dados

Este projeto foi concebido como uma solução end-to-end, onde fui responsável por todas as etapas, desde o design da arquitetura até a implementação do back-end e front-end.

O fluxo de dados funciona da seguinte maneira:

1.  **Entrada de Dados**: Médicos parceiros preenchem um **Google Form** com os dados de um novo paciente.
2.  **Armazenamento Inicial**: A resposta é salva automaticamente em uma planilha do **Google Sheets**.
3.  **Sincronização com a Aplicação**: Ao acessar a lista de pacientes, a aplicação **Flask** utiliza a **API do Google Sheets** para buscar novas entradas.
4.  **Persistência de Dados**: A aplicação verifica quais pacientes são novos e os salva no banco de dados **PostgreSQL** (hospedado na Neon), evitando duplicatas.
5.  **Interação do Usuário**: O médico utiliza a interface web para gerenciar cada etapa do processo. Cada formulário preenchido na aplicação salva os dados em tabelas relacionais no banco de dados.
6.  **Sincronização de Exclusão**: Se um paciente é excluído na aplicação, uma chamada de API é feita para remover a linha correspondente no Google Sheets, mantendo a integridade entre as plataformas.

***

## 🛠️ Tech Stack

A escolha das tecnologias foi focada em robustez, escalabilidade e produtividade.

-   **Back-end**:
    -   **Python**: Linguagem principal da aplicação.
    -   **Flask**: Micro-framework web para construir as rotas, a lógica de negócio e a API interna.
    -   **SQLAlchemy**: ORM para mapeamento objeto-relacional e interação com o banco de dados de forma segura e eficiente.
    -   **Google API Client Library for Python**: Para integração robusta com a API do Google Sheets.

-   **Front-end**:
    -   **HTML5**: Estrutura semântica das páginas.
    -   **CSS3**: Estilização customizada e responsividade (com Flexbox e Media Queries).
    -   **JavaScript (Vanilla)**: Para interatividade no cliente, como o sistema de login assíncrono e a geração de PDF.

-   **Banco de Dados**:
    -   **PostgreSQL (Neon)**: Banco de dados relacional serverless para armazenar de forma persistente e segura os dados dos pacientes e seus respectivos estágios.

-   **APIs e Bibliotecas**:
    -   `Google Sheets API v4`
    -   `jsPDF` & `html2canvas` para a funcionalidade de exportação.

***

## 🗃️ Estrutura do Banco de Dados

O banco de dados foi modelado de forma relacional para garantir a integridade e a organização dos dados.

-   **`FormResponse`**: Tabela central que armazena os dados iniciais do paciente importados do Google Sheets.
-   **Tabelas de Etapas**: `CaseEvaluation`, `Authorization`, `ProcedureExecution`, `FollowUp`.
    -   Cada uma dessas tabelas possui um relacionamento **um-para-um** com a tabela `FormResponse`.
    -   A configuração `cascade="all, delete-orphan"` garante que, ao deletar um paciente, todos os seus registros de etapas associados sejam automaticamente removidos, mantendo a consistência do banco.

***

## 🚀 Como Executar Localmente

Siga os passos abaixo para configurar e executar o projeto em seu ambiente local.

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/seu-usuario/cathped.git](https://github.com/seu-usuario/cathped.git)
    cd cathped
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as variáveis de ambiente:**
    Crie um arquivo `.env` na raiz do projeto e adicione as seguintes variáveis:

    ```env
    # Chave para a sessão do Flask (pode ser qualquer string aleatória)
    secret_key='SUA_CHAVE_SECRETA_AQUI'

    # URI de conexão com seu banco de dados PostgreSQL
    SQLALCHEMY_DATABASE_URI='postgresql://user:password@host:port/database'

    # Credenciais de login da aplicação
    APP_USERNAME='seu_usuario_de_login'
    APP_PASSWORD='sua_senha_de_login'

    # Configurações da API do Google
    SPREADSHEET_ID='ID_DA_SUA_PLANILHA_GOOGLE'
    # Conteúdo completo do seu arquivo JSON de credenciais da conta de serviço, como uma string de linha única.
    CREDENTIALS_FILE='{"type": "service_account", "project_id": "...", ...}'
    ```
    > **Nota**: Para obter as `CREDENTIALS_FILE`, você precisa criar um projeto no Google Cloud Platform, ativar a API do Google Sheets e criar uma conta de serviço. Faça o download do arquivo JSON de credenciais e compartilhe sua planilha com o email da conta de serviço.

5.  **Execute a aplicação:**
    ```bash
    flask run
    ```
    Acesse `http://127.0.0.1:5000` em seu navegador.