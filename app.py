# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# SEÇÃO DE IMPORTAÇÕES
# ---------------------------------------------------------------------------
# Importa as classes e funções necessárias das bibliotecas.
from flask import Flask, render_template, session, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy  # ORM para interagir com o banco de dados
import os  # Para acessar variáveis de ambiente (chaves, senhas, etc.)
import json  # Para manipular dados no formato JSON (usado nas credenciais do Google)
from datetime import datetime  # Para trabalhar com datas e horas
from functools import wraps  # Ferramenta para criar 'decorators' (usado no login_required)
import requests  # (Não utilizado no código, mas geralmente para fazer requisições HTTP)

# Importa as bibliotecas do Google para interagir com a API do Google Sheets
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ---------------------------------------------------------------------------
# CONFIGURAÇÃO INICIAL DO FLASK E BANCO DE DADOS
# ---------------------------------------------------------------------------

# Cria a instância principal da aplicação Flask.
# '__name__' é uma variável especial do Python que obtém o nome do módulo atual.
app = Flask(__name__)

# Configura a URI (endereço) do banco de dados. Este valor é pego de uma variável de ambiente
# para não deixar informações sensíveis diretamente no código.
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')

# Desativa uma funcionalidade do SQLAlchemy que rastreia modificações, economizando recursos.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Define a chave secreta da aplicação, também pega de uma variável de ambiente.
# Essencial para gerenciar sessões de usuário (manter o login).
app.secret_key = os.getenv('secret_key')

# Importa os modelos de dados (tabelas) do arquivo 'models.py' e inicializa o banco.
from models import db, FormResponse, CaseEvaluation, Authorization, ProcedureExecution, FollowUp
db.init_app(app)

# Cria todas as tabelas no banco de dados, caso elas ainda não existam.
# 'with app.app_context()' garante que a aplicação Flask esteja configurada corretamente
# antes de tentar interagir com o banco de dados.
with app.app_context():
    db.create_all()

# ---------------------------------------------------------------------------
# CONFIGURAÇÕES DA API DO GOOGLE SHEETS
# ---------------------------------------------------------------------------

# ID da planilha do Google de onde os dados serão lidos.
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
# Intervalo de células a ser lido (ex: da coluna A até a K da aba 'Respostas ao formulário 1').
RANGE_NAME = 'Respostas ao formulário 1!A:K'
# Conteúdo do arquivo JSON de credenciais, armazenado como uma variável de ambiente.
CREDENTIALS_FILE = os.getenv('CREDENTIALS_FILE')

# Define os "escopos" de permissão. Aqui, estamos pedindo permissão para ler e escrever em planilhas.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


# ---------------------------------------------------------------------------
# FUNÇÕES DE INTERAÇÃO COM O GOOGLE SHEETS
# ---------------------------------------------------------------------------

def get_google_sheet_service():
    """
    Autentica e cria o objeto de serviço para interagir com a API do Google Sheets.
    Usa as credenciais de uma conta de serviço armazenadas em uma variável de ambiente.
    """
    # 1. Verifica se a variável de ambiente com as credenciais foi definida.
    if not CREDENTIALS_FILE:
        raise ValueError("A variável de ambiente 'CREDENTIALS_FILE' não foi definida ou está vazia.")

    # 2. Converte a string JSON da variável de ambiente para um dicionário Python.
    credentials_info = json.loads(CREDENTIALS_FILE)

    # 3. Cria o objeto de credenciais a partir do dicionário.
    creds = service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=SCOPES
    )
    
    # 4. Constrói e retorna o objeto de serviço que será usado para fazer as chamadas à API.
    return build('sheets', 'v4', credentials=creds, cache_discovery=False)

def fetch_responses():
    """
    Busca novas respostas da planilha do Google, verifica se já existem no banco de dados local
    e insere apenas as que forem novas.
    """
    try:
        # Obtém o serviço autenticado do Google Sheets.
        service = get_google_sheet_service()
        sheet = service.spreadsheets()

        # Executa a chamada à API para obter os valores da planilha.
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        responses = result.get('values', []) # Pega a lista de linhas; se não houver, retorna lista vazia.

        # Se a planilha estiver vazia, imprime um aviso e encerra a função.
        if not responses:
            print("Nenhum dado encontrado na planilha!")
            return 0

        # Ignora a primeira linha (cabeçalho da tabela).
        responses = responses[1:] 
        new_entries = 0 # Contador para novas entradas.

        # Itera sobre cada linha de resposta da planilha.
        for row in responses:
            # Pula a linha se ela não tiver o número mínimo de colunas esperadas (11).
            if len(row) < 11:
                print(f"Erro: Linha incompleta -> {row}")
                continue
            
            # Verifica se já existe um paciente com o mesmo nome no banco de dados.
            # 'row[2]' corresponde à coluna do nome completo do paciente.
            existing_patient = FormResponse.query.filter_by(patient_full_name=row[2]).first()
            if existing_patient:
                continue # Se já existe, pula para a próxima linha.

            # Se o paciente é novo, cria um objeto 'FormResponse' com os dados da linha.
            try:
                response = FormResponse(
                    email=row[1],
                    patient_full_name=row[2],
                    patient_age=int(row[3]),
                    patient_contact=str(row[4]),
                    referral_date=parse_date(row[5]), # Usa a função auxiliar para converter a data.
                    internment_type=row[6],
                    location=row[7],
                    procedure=row[8],
                    diagnosis=row[9],
                    condition_severity=row[10]
                )
                # Adiciona o novo objeto à sessão do banco de dados (prepara para salvar).
                db.session.add(response)
                new_entries += 1
            except Exception as e:
                # Captura e informa erros que possam ocorrer durante a conversão dos dados da linha.
                print(f"Erro ao processar a linha {row}: {e}")

        # Salva todas as novas entradas adicionadas no banco de dados.
        db.session.commit()
        return new_entries

    except Exception as e:
        # Captura e informa qualquer erro que ocorra na comunicação com a API do Google.
        print(f"Erro ao buscar dados do Google Sheets: {e}")
        return 0

def get_sheet_id():
    """
    Obtém o ID numérico da aba (sheet) específica pelo seu nome.
    Este ID é necessário para operações como deletar uma linha.
    """
    try:
        service = get_google_sheet_service()
        # Obtém os metadados da planilha inteira.
        spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        sheets = spreadsheet.get("sheets", [])

        # Procura a aba com o título "Respostas ao formulário 1".
        for sheet in sheets:
            if sheet["properties"]["title"] == "Respostas ao formulário 1":
                return sheet["properties"]["sheetId"] # Retorna o ID encontrado.

        print("Erro: Aba 'Respostas ao formulário 1' não foi encontrada.")
        return None

    except Exception as e:
        print(f"Ocorreu um erro ao tentar obter o sheetId: {e}")
        return None

def parse_date(value):
    """
    Função auxiliar para converter strings de data em diferentes formatos
    para um objeto de data do Python.
    """
    if value is None:
        return None
    
    # Tenta converter o formato "dd/mm/yyyy".
    try:
        return datetime.strptime(value, "%d/%m/%Y").date()
    except ValueError:
        pass # Se falhar, tenta o próximo formato.

    # Tenta converter o formato "Date(YYYY,MM,DD)" que algumas planilhas geram.
    try:
        if value.startswith("Date(") and value.endswith(")"):
            parts = value[5:-1].split(",")
            year, month, day = map(int, parts)
            return datetime(year, month, day).date()
    except Exception:
        pass
    
    # Se nenhum formato for reconhecido, retorna None.
    return None

# ---------------------------------------------------------------------------
# DECORATOR DE LOGIN
# ---------------------------------------------------------------------------
# Um 'decorator' é uma função que "envolve" outra função para adicionar
# uma funcionalidade extra antes ou depois da execução dela.

def login_required(f):
    @wraps(f) # Preserva o nome e outras propriedades da função original.
    def decorated_function(*args, **kwargs):
        # Verifica se a chave 'logged_in' não está na sessão do usuário.
        if not session.get('logged_in'):
            # Se não estiver logado, redireciona para a página inicial (login).
            return redirect(url_for('home'))
        # Se estiver logado, executa a função original (a rota protegida).
        return f(*args, **kwargs)
    return decorated_function

# ---------------------------------------------------------------------------
# ROTAS DE AUTENTICAÇÃO E SESSÃO
# ---------------------------------------------------------------------------

# Pega o usuário e senha da aplicação das variáveis de ambiente.
APP_USERNAME = os.getenv('APP_USERNAME')
APP_PASSWORD = os.getenv('APP_PASSWORD')

@app.route('/', methods=['GET'])
def home():
    """Renderiza a página inicial, que serve como tela de login."""
    return render_template('index.html')

@app.route('/login', methods=['GET'])
def login_page():
    """Redireciona para a home se alguém tentar acessar /login via GET."""
    return redirect(url_for('home'))

@app.route('/login', methods=['POST'])
def login():
    """
    Processa a tentativa de login enviada pelo formulário (via JavaScript/fetch).
    Recebe os dados em formato JSON.
    """
    data = request.get_json() # Pega os dados JSON da requisição.
    username = data.get('username')
    password = data.get('password')

    # Compara o usuário e senha recebidos com os valores definidos nas variáveis de ambiente.
    if username == APP_USERNAME and password == APP_PASSWORD:
        session['logged_in'] = True # Se correto, marca a sessão como 'logada'.
        return jsonify({'success': True}) # Retorna sucesso em JSON para o JavaScript.
    else:
        # Se incorreto, retorna uma mensagem de erro.
        return jsonify({'success': False, 'message': 'Usuário ou senha incorretos'}), 401

@app.route('/check_session')
def check_session():
    """
    Uma rota auxiliar para o front-end verificar se o usuário já está logado
    (útil ao recarregar a página).
    """
    return jsonify({'logged_in': session.get('logged_in', False)})

# ---------------------------------------------------------------------------
# ROTAS PRINCIPAIS DA APLICAÇÃO
# ---------------------------------------------------------------------------

@app.route('/listpatient')
@login_required # Protege esta rota: só pode ser acessada por usuários logados.
def list_patients():
    """
    Exibe a lista de pacientes. Primeiro, sincroniza com a planilha do Google
    para buscar novos pacientes.
    """
    # Chama a função para buscar e adicionar novos pacientes da planilha.
    new_entries = fetch_responses()
    print(f"{new_entries} novo(s) paciente(s) adicionado(s) antes de exibir a lista.")

    # Pega o termo de busca da URL (ex: /listpatient?search=Maria).
    search_query = request.args.get('search', '')
    if search_query:
        # Se houver busca, filtra os pacientes cujo nome contenha o termo buscado (ignorando maiúsculas/minúsculas).
        patients = FormResponse.query.filter(FormResponse.patient_full_name.ilike(f"%{search_query}%")).all()
    else:
        # Se não houver busca, pega todos os pacientes.
        patients = FormResponse.query.all()

    # Renderiza o template 'listpatient.html', passando a lista de pacientes e o termo de busca.
    return render_template('listpatient.html', patients=patients, search_query=search_query)

def remove_patient_from_google_sheets(full_name):
    """
    Remove a linha correspondente a um paciente da planilha do Google.
    """
    try:
        service = get_google_sheet_service()
        sheet = service.spreadsheets()
        
        # Obtém o ID numérico da aba, necessário para a exclusão.
        sheet_id = get_sheet_id()
        if sheet_id is None:
            print("Erro: ID da planilha não encontrado.")
            return False

        # Pega todos os valores da planilha para encontrar a linha a ser deletada.
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get('values', [])

        if not values:
            print("A planilha estava vazia ou ocorreu um erro ao buscar os dados.")
            return False

        # Encontra o índice da linha onde o nome do paciente corresponde.
        row_to_delete = None
        for i, row in enumerate(values):
            # Compara o nome na coluna 2 (índice), ignorando espaços extras e maiúsculas/minúsculas.
            if len(row) > 2 and row[2].strip().lower() == full_name.strip().lower():
                row_to_delete = i # Armazena o índice da linha.
                break

        # Se a linha foi encontrada, monta e executa o pedido de exclusão.
        if row_to_delete is not None:
            batch_update_request = {
                "requests": [{
                    "deleteDimension": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "ROWS", # Queremos deletar uma linha.
                            "startIndex": row_to_delete, # Índice inicial da linha.
                            "endIndex": row_to_delete + 1 # Índice final (exclusivo).
                        }
                    }
                }]
            }
            # Envia a requisição para a API para deletar a linha.
            sheet.batchUpdate(spreadsheetId=SPREADSHEET_ID, body=batch_update_request).execute()
            print(f"Paciente com nome {full_name} foi removido da planilha Google Sheets.")
            return True
        else:
            print(f"Paciente com nome {full_name} não foi encontrado na planilha.")
            return False

    except Exception as e:
        print(f"Ocorreu um erro ao tentar remover do Google Sheets: {e}")
        return False

@app.route('/delete_patient/<int:patient_id>', methods=['POST'])
@login_required
def delete_patient(patient_id):
    """
    Deleta um paciente tanto do banco de dados local quanto da planilha do Google.
    """
    # Encontra o paciente no banco de dados. Se não achar, retorna erro 404.
    patient = FormResponse.query.get_or_404(patient_id)
    
    if patient:
        full_name = patient.patient_full_name
        # Deleta o paciente do banco de dados local.
        db.session.delete(patient)
        db.session.commit()
        print(f"Paciente {full_name} foi removido do banco de dados.")

        # Chama a função para remover também da planilha do Google.
        remove_patient_from_google_sheets(full_name)

    # Redireciona de volta para a lista de pacientes.
    return redirect(url_for('list_patients'))

# ---------------------------------------------------------------------------
# ROTAS DOS FORMULÁRIOS DE ETAPAS DO PROCESSO
# ---------------------------------------------------------------------------
# As rotas a seguir seguem um padrão:
# - Recebem um 'patient_id' pela URL.
# - Se o método for GET, exibem o formulário correspondente.
# - Se o método for POST, processam os dados do formulário, salvam no banco
#   de dados e redirecionam para a lista de pacientes.

@app.route('/case_evaluation/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def case_evaluation(patient_id):
    """Rota para o formulário de Avaliação do Caso."""
    patient = FormResponse.query.get_or_404(patient_id)

    if request.method == 'POST':
        # Coleta os dados do formulário enviado.
        evaluation_date = datetime.strptime(request.form['evaluation_date'], '%Y-%m-%d').date()
        diagnosis_2 = request.form['diagnosis_2']
        severity = request.form['severity']
        procedure_requested = request.form['procedure_requested']
        requester = request.form['requester']
        opme_needed = request.form.get('opme_needed') == 'True'
        special_opme = request.form.get('special_opme') == 'True'
        previous_complications = request.form.get('previous_complications') == 'True'

        # Cria uma nova instância do modelo CaseEvaluation.
        case_eval = CaseEvaluation(
            patient_id=patient.id,
            evaluation_date=evaluation_date,
            diagnosis_2=diagnosis_2,
            severity=severity,
            procedure_requested=procedure_requested,
            requester=requester,
            opme_needed=opme_needed,
            special_opme=special_opme,
            previous_complications=previous_complications
        )
        # Salva no banco de dados.
        db.session.add(case_eval)
        db.session.commit()
        flash("Avaliação de caso salva com sucesso!", "success")
        return redirect(url_for('list_patients'))

    # Se for GET, apenas renderiza a página do formulário.
    return render_template('case_evaluation.html', patient=patient)


@app.route('/authorization/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def authorization(patient_id):
    """Rota para o formulário de Autorização."""
    patient = FormResponse.query.get_or_404(patient_id)

    if request.method == 'POST':
        # Converte o valor do checkbox 'on' para True/False.
        opme_authorization = request.form.get('opme_authorization') == 'on'

        # Converte as strings de data e hora para os tipos corretos, tratando campos vazios.
        scheduling_date = datetime.strptime(request.form['scheduling_date'], '%Y-%m-%d').date() if request.form['scheduling_date'] else None
        execution_date = datetime.strptime(request.form['execution_date'], '%Y-%m-%d').date() if request.form['execution_date'] else None
        execution_time = datetime.strptime(request.form['execution_time'], '%H:%M').time() if request.form['execution_time'] else None
        cancellation_reason = request.form.get('cancellation_reason', '')

        # Cria a instância do modelo e salva no banco.
        auth = Authorization(
            patient_id=patient.id,
            opme_authorization=opme_authorization,
            scheduling_date=scheduling_date,
            execution_date=execution_date,
            execution_time=execution_time,
            cancellation_reason=cancellation_reason
        )
        db.session.add(auth)
        db.session.commit()
        flash("Autorização salva com sucesso!", "success")
        return redirect(url_for('list_patients'))

    return render_template('authorization.html', patient=patient)


@app.route('/procedure_execution/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def procedure_execution(patient_id):
    """Rota para o formulário de Execução do Procedimento."""
    patient = FormResponse.query.get_or_404(patient_id)

    if request.method == 'POST':
        # Coleta e processa os dados do formulário.
        execution_date = datetime.strptime(request.form['execution_date'], '%Y-%m-%d').date()
        medical_report = request.form['medical_report']
        patient_informed = request.form.get('patient_informed') == 'on'
        previous_complications = request.form.get('previous_complications') == 'on'

        # Cria a instância do modelo e salva no banco.
        procedure = ProcedureExecution(
            patient_id=patient.id,
            execution_date=execution_date,
            medical_report=medical_report,
            patient_informed=patient_informed,
            previous_complications=previous_complications
        )
        db.session.add(procedure)
        db.session.commit()
        flash("Execução de procedimento salva com sucesso!", "success")
        return redirect(url_for('list_patients'))

    return render_template('procedure_execution.html', patient=patient)


@app.route('/follow_up/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def follow_up(patient_id):
    """Rota para o formulário de Acompanhamento Pós-Procedimento."""
    patient = FormResponse.query.get_or_404(patient_id)

    if request.method == 'POST':
        # Coleta e processa os dados do formulário.
        post_procedure_complications = request.form.get('post_procedure_complications') == 'on'
        
        # Cria a instância do modelo e salva no banco.
        followup = FollowUp(
            patient_id=patient.id,
            post_procedure_complications=post_procedure_complications
        )
        db.session.add(followup)
        db.session.commit()
        flash("Acompanhamento pós-procedimento salvo com sucesso!", "success")
        return redirect(url_for('list_patients'))

    return render_template('follow_up.html', patient=patient)


@app.route('/patient_summary/<int:patient_id>', methods=['GET'])
@login_required
def patient_summary(patient_id):
    """
    Exibe uma página com o resumo completo de todas as informações de um paciente.
    """
    # Busca o paciente principal.
    patient = FormResponse.query.get_or_404(patient_id)

    # Busca os dados de cada etapa do processo relacionados a este paciente.
    # '.first()' é usado porque esperamos no máximo um registro por etapa para cada paciente.
    case_evaluation = CaseEvaluation.query.filter_by(patient_id=patient_id).first()
    authorization = Authorization.query.filter_by(patient_id=patient_id).first()
    procedure_execution = ProcedureExecution.query.filter_by(patient_id=patient_id).first()
    follow_up = FollowUp.query.filter_by(patient_id=patient_id).first()

    # Renderiza a página de resumo, passando todos os objetos de dados encontrados.
    return render_template(
        'patient_summary.html',
        patient=patient,
        case_evaluation=case_evaluation,
        authorization=authorization,
        procedure_execution=procedure_execution,
        follow_up=follow_up
    )

# ---------------------------------------------------------------------------
# INICIALIZAÇÃO DA APLICAÇÃO
# ---------------------------------------------------------------------------

# Este bloco só é executado quando o script 'app.py' é rodado diretamente.
if __name__ == '__main__':
    # Inicia o servidor de desenvolvimento do Flask.
    # 'debug=True' ativa o modo de depuração, que reinicia o servidor automaticamente
    # a cada mudança no código e mostra erros detalhados no navegador.
    app.run(debug=True)
