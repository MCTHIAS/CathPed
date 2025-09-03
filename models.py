# -*- coding: utf-8 -*-

# Importa a classe SQLAlchemy, que é a principal ferramenta do Flask-SQLAlchemy
# para interagir com o banco de dados.
from flask_sqlalchemy import SQLAlchemy

# Cria uma instância do SQLAlchemy. Esta instância 'db' será usada em toda a aplicação
# para definir modelos (tabelas) e executar consultas no banco de dados.
db = SQLAlchemy()

# ---------------------------------------------------------------------------
# MODELO: FormResponse
# DESCRIÇÃO: Representa a tabela principal que armazena os dados iniciais do paciente,
#            vindos do formulário do Google Sheets. É a "tabela-mãe" do sistema.
# ---------------------------------------------------------------------------
class FormResponse(db.Model):
    # Define as colunas da tabela 'form_response' no banco de dados.

    # 'id': Chave primária. Um número inteiro único que identifica cada registro.
    id = db.Column(db.Integer, primary_key=True)
    
    # 'patient_full_name': Nome completo do paciente. String com até 200 caracteres, não pode ser nulo.
    patient_full_name = db.Column(db.String(200), nullable=False)
    
    # 'patient_age': Idade do paciente. Número inteiro, não pode ser nulo.
    patient_age = db.Column(db.Integer, nullable=False)
    
    # 'patient_contact': Contato do paciente. String com até 15 caracteres, não pode ser nulo.
    patient_contact = db.Column(db.String(15), nullable=False)
    
    # 'referral_date': Data do encaminhamento. Armazena apenas a data, não pode ser nulo.
    referral_date = db.Column(db.Date, nullable=False)
    
    # 'internment_type': Tipo de internação. String com até 50 caracteres, não pode ser nulo.
    internment_type = db.Column(db.String(50), nullable=False)
    
    # 'location': Localização do paciente. String com até 200 caracteres, não pode ser nulo.
    location = db.Column(db.String(200), nullable=False)
    
    # 'procedure': Procedimento inicial. String com até 200 caracteres, não pode ser nulo.
    procedure = db.Column(db.String(200), nullable=False)
    
    # 'diagnosis': Diagnóstico inicial. Campo de texto longo, não pode ser nulo.
    diagnosis = db.Column(db.Text, nullable=False)
    
    # 'condition_severity': Gravidade da condição. String com até 200 caracteres, não pode ser nulo.
    condition_severity = db.Column(db.String(200), nullable=False)
    
    # 'email': E-mail de quem preencheu o formulário. Pode ser nulo.
    email = db.Column(db.String(200), nullable=True)

    # --- RELACIONAMENTOS ---
    # Define as ligações entre esta tabela (FormResponse) e as outras tabelas do sistema.
    # Estes relacionamentos permitem acessar os dados das tabelas filhas diretamente a partir de um objeto paciente.

    # 'case_evaluation': Relacionamento um-para-um com a tabela CaseEvaluation.
    # 'backref='patient'': Permite que um objeto CaseEvaluation acesse o FormResponse pai através do atributo '.patient'.
    # 'uselist=False': Especifica que este é um relacionamento um-para-um (cada paciente tem no máximo uma avaliação).
    # 'cascade="all, delete-orphan"': Regra importante! Se um paciente (FormResponse) for deletado,
    #                                  sua avaliação de caso associada também será deletada automaticamente.
    case_evaluation = db.relationship('CaseEvaluation', backref='patient', uselist=False, cascade="all, delete-orphan")
    authorization = db.relationship('Authorization', backref='patient', uselist=False, cascade="all, delete-orphan")
    procedure_execution = db.relationship('ProcedureExecution', backref='patient', uselist=False, cascade="all, delete-orphan")
    follow_up = db.relationship('FollowUp', backref='patient', uselist=False, cascade="all, delete-orphan")

    # --- MÉTODOS AUXILIARES ---
    # Funções úteis para verificar o status do fluxo de um paciente nos templates HTML.

    def is_case_evaluation_done(self):
        """Verifica se já existe uma avaliação de caso para este paciente."""
        return self.case_evaluation is not None

    def is_authorization_done(self):
        """Verifica se já existe uma autorização para este paciente."""
        return self.authorization is not None

    def is_procedure_execution_done(self):
        """Verifica se já existe um registro de execução de procedimento para este paciente."""
        return self.procedure_execution is not None

    def is_follow_up_done(self):
        """Verifica se já existe um registro de acompanhamento para este paciente."""
        return self.follow_up is not None

# ---------------------------------------------------------------------------
# MODELO: CaseEvaluation
# DESCRIÇÃO: Armazena os dados do formulário "Avaliação de Caso".
# ---------------------------------------------------------------------------
class CaseEvaluation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # 'patient_id': Chave estrangeira. Liga este registro a um paciente específico na tabela 'form_response'.
    # 'db.ForeignKey('form_response.id')' cria a restrição no nível do banco de dados.
    patient_id = db.Column(db.Integer, db.ForeignKey('form_response.id'), nullable=False)
    
    evaluation_date = db.Column(db.Date, nullable=False)
    diagnosis_2 = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    procedure_requested = db.Column(db.String(100), nullable=False)
    requester = db.Column(db.String(200), nullable=True) # Pode ser nulo
    
    # Campos booleanos (verdadeiro/falso) para checkboxes.
    opme_needed = db.Column(db.Boolean, nullable=False)
    special_opme = db.Column(db.Boolean, nullable=False)
    previous_complications = db.Column(db.Boolean, nullable=False)

# ---------------------------------------------------------------------------
# MODELO: Authorization
# DESCRIÇÃO: Armazena os dados do formulário "Autorização".
# ---------------------------------------------------------------------------
class Authorization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('form_response.id'), nullable=False)
    
    opme_authorization = db.Column(db.Boolean, nullable=False)
    
    # Campos de data e hora que podem ser nulos (caso ainda não tenham sido definidos).
    scheduling_date = db.Column(db.Date, nullable=True)
    execution_date = db.Column(db.Date, nullable=True)
    execution_time = db.Column(db.Time, nullable=True)
    cancellation_reason = db.Column(db.Text, nullable=True)

# ---------------------------------------------------------------------------
# MODELO: ProcedureExecution
# DESCRIÇÃO: Armazena os dados do formulário "Execução do Procedimento".
# ---------------------------------------------------------------------------
class ProcedureExecution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('form_response.id'), nullable=False)
    
    execution_date = db.Column(db.Date, nullable=False)
    medical_report = db.Column(db.Text, nullable=True)
    patient_informed = db.Column(db.Boolean, nullable=False)
    previous_complications = db.Column(db.Boolean, nullable=False)

# ---------------------------------------------------------------------------
# MODELO: FollowUp
# DESCRIÇÃO: Armazena os dados do formulário "Acompanhamento Pós-Procedimento".
# ---------------------------------------------------------------------------
class FollowUp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('form_response.id'), nullable=False)
    
    post_procedure_complications = db.Column(db.Boolean, nullable=False)
