from flask import Blueprint, request, jsonify
from src.models.evaluation import db, HealthUnit, Preceptor, Student, StudentGroup, GroupMembership, EvaluationDate, Evaluation
from datetime import datetime, date

evaluation_bp = Blueprint('evaluation', __name__)

# CORS headers
@evaluation_bp.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@evaluation_bp.route('/health-units', methods=['GET', 'POST'])
def health_units():
    if request.method == 'GET':
        units = HealthUnit.query.all()
        return jsonify([unit.to_dict() for unit in units])
    
    elif request.method == 'POST':
        data = request.get_json()
        unit = HealthUnit(name=data['name'])
        db.session.add(unit)
        db.session.commit()
        return jsonify(unit.to_dict()), 201

@evaluation_bp.route('/preceptors', methods=['GET', 'POST'])
def preceptors():
    if request.method == 'GET':
        preceptors = Preceptor.query.all()
        return jsonify([preceptor.to_dict() for preceptor in preceptors])
    
    elif request.method == 'POST':
        data = request.get_json()
        preceptor = Preceptor(
            name=data['name'],
            email=data.get('email')
        )
        db.session.add(preceptor)
        db.session.commit()
        return jsonify(preceptor.to_dict()), 201

@evaluation_bp.route('/students', methods=['GET', 'POST'])
def students():
    if request.method == 'GET':
        students = Student.query.all()
        return jsonify([student.to_dict() for student in students])
    
    elif request.method == 'POST':
        data = request.get_json()
        student = Student(
            name=data['name'],
            registration=data.get('registration')
        )
        db.session.add(student)
        db.session.commit()
        return jsonify(student.to_dict()), 201

@evaluation_bp.route('/groups', methods=['GET', 'POST'])
def groups():
    if request.method == 'GET':
        groups = StudentGroup.query.all()
        return jsonify([group.to_dict() for group in groups])
    
    elif request.method == 'POST':
        data = request.get_json()
        group = StudentGroup(
            name=data['name'],
            period=data['period'],
            year=data['year'],
            semester=data['semester'],
            health_unit_id=data['health_unit_id'],
            preceptor_id=data['preceptor_id']
        )
        db.session.add(group)
        db.session.commit()
        return jsonify(group.to_dict()), 201

@evaluation_bp.route('/groups/<int:group_id>/students', methods=['GET', 'POST'])
def group_students(group_id):
    if request.method == 'GET':
        memberships = GroupMembership.query.filter_by(group_id=group_id).all()
        return jsonify([membership.to_dict() for membership in memberships])
    
    elif request.method == 'POST':
        data = request.get_json()
        membership = GroupMembership(
            student_id=data['student_id'],
            group_id=group_id
        )
        db.session.add(membership)
        db.session.commit()
        return jsonify(membership.to_dict()), 201

@evaluation_bp.route('/groups/<int:group_id>/evaluation-dates', methods=['GET', 'POST'])
def evaluation_dates(group_id):
    if request.method == 'GET':
        dates = EvaluationDate.query.filter_by(group_id=group_id).all()
        return jsonify([date.to_dict() for date in dates])
    
    elif request.method == 'POST':
        data = request.get_json()
        eval_date = EvaluationDate(
            group_id=group_id,
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            description=data.get('description')
        )
        db.session.add(eval_date)
        db.session.commit()
        return jsonify(eval_date.to_dict()), 201

@evaluation_bp.route('/evaluations', methods=['GET', 'POST'])
def evaluations():
    if request.method == 'GET':
        student_id = request.args.get('student_id')
        group_id = request.args.get('group_id')
        
        query = Evaluation.query
        
        if student_id:
            query = query.filter_by(student_id=student_id)
        
        if group_id:
            query = query.join(EvaluationDate).filter(EvaluationDate.group_id == group_id)
        
        evaluations = query.all()
        return jsonify([evaluation.to_dict() for evaluation in evaluations])
    
    elif request.method == 'POST':
        data = request.get_json()
        evaluation = Evaluation(
            student_id=data['student_id'],
            evaluation_date_id=data['evaluation_date_id'],
            attitude_score=data.get('attitude_score'),
            skill_score=data.get('skill_score'),
            cognition_score=data.get('cognition_score'),
            observations=data.get('observations')
        )
        db.session.add(evaluation)
        db.session.commit()
        return jsonify(evaluation.to_dict()), 201

@evaluation_bp.route('/evaluations/<int:evaluation_id>', methods=['PUT', 'DELETE'])
def evaluation_detail(evaluation_id):
    evaluation = Evaluation.query.get_or_404(evaluation_id)
    
    if request.method == 'PUT':
        data = request.get_json()
        evaluation.attitude_score = data.get('attitude_score', evaluation.attitude_score)
        evaluation.skill_score = data.get('skill_score', evaluation.skill_score)
        evaluation.cognition_score = data.get('cognition_score', evaluation.cognition_score)
        evaluation.observations = data.get('observations', evaluation.observations)
        evaluation.updated_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify(evaluation.to_dict())
    
    elif request.method == 'DELETE':
        db.session.delete(evaluation)
        db.session.commit()
        return '', 204

@evaluation_bp.route('/groups/<int:group_id>/report', methods=['GET'])
def group_report(group_id):
    """Gera relatório completo do grupo"""
    group = StudentGroup.query.get_or_404(group_id)
    
    # Buscar todos os membros do grupo
    memberships = GroupMembership.query.filter_by(group_id=group_id).all()
    students = [membership.student for membership in memberships]
    
    # Buscar todas as datas de avaliação
    eval_dates = EvaluationDate.query.filter_by(group_id=group_id).order_by(EvaluationDate.date).all()
    
    # Buscar todas as avaliações
    evaluations = Evaluation.query.join(EvaluationDate).filter(EvaluationDate.group_id == group_id).all()
    
    # Organizar dados por aluno
    report_data = {
        'group': group.to_dict(),
        'students': [],
        'evaluation_dates': [date.to_dict() for date in eval_dates]
    }
    
    for student in students:
        student_data = student.to_dict()
        student_evaluations = [eval for eval in evaluations if eval.student_id == student.id]
        
        # Organizar avaliações por data
        evaluations_by_date = {}
        for evaluation in student_evaluations:
            date_id = evaluation.evaluation_date_id
            evaluations_by_date[date_id] = evaluation.to_dict()
        
        student_data['evaluations'] = evaluations_by_date
        
        # Calcular médias
        attitude_scores = [eval.attitude_score for eval in student_evaluations if eval.attitude_score is not None]
        skill_scores = [eval.skill_score for eval in student_evaluations if eval.skill_score is not None]
        cognition_scores = [eval.cognition_score for eval in student_evaluations if eval.cognition_score is not None]
        
        student_data['averages'] = {
            'attitude': sum(attitude_scores) / len(attitude_scores) if attitude_scores else None,
            'skill': sum(skill_scores) / len(skill_scores) if skill_scores else None,
            'cognition': sum(cognition_scores) / len(cognition_scores) if cognition_scores else None
        }
        
        # Calcular média geral
        all_scores = attitude_scores + skill_scores + cognition_scores
        student_data['overall_average'] = sum(all_scores) / len(all_scores) if all_scores else None
        
        report_data['students'].append(student_data)
    
    return jsonify(report_data)

@evaluation_bp.route('/import-spreadsheet', methods=['POST'])
def import_spreadsheet():
    """Importa dados da planilha fornecida"""
    try:
        # Criar unidade de saúde
        health_unit = HealthUnit(name="UNIDADE DE SAÚDE DA FAMÍLIA DO BOM TEMPO")
        db.session.add(health_unit)
        db.session.flush()
        
        # Criar preceptor
        preceptor = Preceptor(name="DR Renê Carvalho de Brito")
        db.session.add(preceptor)
        db.session.flush()
        
        # Criar grupo
        group = StudentGroup(
            name="8ª ETAPA DO PIESF (Terças-feiras)",
            period="8ª ETAPA",
            year=2025,
            semester=1,
            health_unit_id=health_unit.id,
            preceptor_id=preceptor.id
        )
        db.session.add(group)
        db.session.flush()
        
        # Criar alunos
        students_data = [
            {"name": "ISABELA PEREIRA"},
            {"name": "INGRID MACEDO"}
        ]
        
        students = []
        for student_data in students_data:
            student = Student(name=student_data["name"])
            db.session.add(student)
            db.session.flush()
            students.append(student)
            
            # Adicionar ao grupo
            membership = GroupMembership(student_id=student.id, group_id=group.id)
            db.session.add(membership)
        
        # Criar datas de avaliação
        evaluation_dates_data = [
            "2025-02-11", "2025-02-25", "2025-03-18", "2025-04-01",
            "2025-04-15", "2025-04-29", "2025-05-13", "2025-05-27", "2025-06-10"
        ]
        
        eval_dates = []
        for date_str in evaluation_dates_data:
            eval_date = EvaluationDate(
                group_id=group.id,
                date=datetime.strptime(date_str, '%Y-%m-%d').date()
            )
            db.session.add(eval_date)
            db.session.flush()
            eval_dates.append(eval_date)
        
        # Criar avaliações de exemplo (Isabela)
        isabela_scores = [
            {"attitude": 10, "skill": 10, "cognition": 10},
            {"attitude": 10, "skill": 10, "cognition": 10},
            {"attitude": 10, "skill": 10, "cognition": 10},
            {"attitude": 10, "skill": 10, "cognition": 10},
            {"attitude": 10, "skill": 10, "cognition": 10},
            {"attitude": 7, "skill": 7, "cognition": 7},
            {"attitude": 10, "skill": 10, "cognition": 10},
            {"attitude": 10, "skill": 10, "cognition": 10},
            {"attitude": 7, "skill": 7, "cognition": 7}
        ]
        
        for i, scores in enumerate(isabela_scores):
            evaluation = Evaluation(
                student_id=students[0].id,
                evaluation_date_id=eval_dates[i].id,
                attitude_score=scores["attitude"],
                skill_score=scores["skill"],
                cognition_score=scores["cognition"]
            )
            db.session.add(evaluation)
        
        # Criar avaliações de exemplo (Ingrid)
        ingrid_scores = [
            {"attitude": 10, "skill": 10, "cognition": 10},
            {"attitude": 10, "skill": 10, "cognition": 10},
            {"attitude": 10, "skill": 10, "cognition": 10},
            {"attitude": 10, "skill": 10, "cognition": 10},
            {"attitude": 10, "skill": 10, "cognition": 10},
            {"attitude": 10, "skill": 10, "cognition": 10},
            {"attitude": 10, "skill": 10, "cognition": 10},
            {"attitude": 10, "skill": 10, "cognition": 10},
            {"attitude": 7, "skill": 7, "cognition": 7}
        ]
        
        for i, scores in enumerate(ingrid_scores):
            evaluation = Evaluation(
                student_id=students[1].id,
                evaluation_date_id=eval_dates[i].id,
                attitude_score=scores["attitude"],
                skill_score=scores["skill"],
                cognition_score=scores["cognition"]
            )
            db.session.add(evaluation)
        
        db.session.commit()
        
        return jsonify({
            "message": "Dados importados com sucesso!",
            "group_id": group.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

