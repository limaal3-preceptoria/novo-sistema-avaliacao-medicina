"""Evaluation blueprint and API endpoints for the application.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from src.models.evaluation import (
    db,
    HealthUnit,
    Preceptor,
    Student,
    StudentGroup,
    GroupMembership,
    EvaluationDate,
    Evaluation,
)

evaluation_bp = Blueprint('evaluation', __name__)


@evaluation_bp.after_request
def after_request(response):
    """Add CORS headers to all responses."""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response


@evaluation_bp.route('/health-units', methods=['GET', 'POST'])
def health_units():
    """List or create health units."""
    if request.method == 'GET':
        units = HealthUnit.query.all()
        return jsonify([unit.to_dict() for unit in units])

    data = request.get_json()
    unit = HealthUnit(name=data['name'])
    db.session.add(unit)
    db.session.commit()
    return jsonify(unit.to_dict()), 201


@evaluation_bp.route('/preceptors', methods=['GET', 'POST'])
def preceptors():
    """List or create preceptors."""
    if request.method == 'GET':
        preceptors_list = Preceptor.query.all()
        return jsonify([preceptor.to_dict() for preceptor in preceptors_list])

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
    """List or create students."""
    if request.method == 'GET':
        students_list = Student.query.all()
        return jsonify([student.to_dict() for student in students_list])

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
    """List or create student groups."""
    if request.method == 'GET':
        groups_list = StudentGroup.query.all()
        return jsonify([group.to_dict() for group in groups_list])

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
    """List or add students to a group."""
    if request.method == 'GET':
        memberships = GroupMembership.query.filter_by(group_id=group_id).all()
        return jsonify([membership.to_dict() for membership in memberships])

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
    """List or create evaluation dates for a group."""
    if request.method == 'GET':
        dates = EvaluationDate.query.filter_by(group_id=group_id).all()
        return jsonify([d.to_dict() for d in dates])

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
    """List or create evaluations."""
    if request.method == 'GET':
        student_id = request.args.get('student_id')
        group_id = request.args.get('group_id')

        query = Evaluation.query

        if student_id:
            query = query.filter_by(student_id=student_id)

        if group_id:
            query = query.join(EvaluationDate).filter(EvaluationDate.group_id == group_id)

        evaluations_list = query.all()
        return jsonify([evaluation.to_dict() for evaluation in evaluations_list])

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
    """Update or delete a specific evaluation."""
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

    db.session.delete(evaluation)
    db.session.commit()
    return '', 204


@evaluation_bp.route('/groups/<int:group_id>/report', methods=['GET'])
def group_report(group_id):
    """Generate a full report for a group."""
    group = StudentGroup.query.get_or_404(group_id)

    memberships = GroupMembership.query.filter_by(group_id=group_id).all()
    group_members = [membership.student for membership in memberships]

    eval_dates = EvaluationDate.query.filter_by(group_id=group_id).order_by(EvaluationDate.date).all()

    group_evaluations = (
        Evaluation.query.join(EvaluationDate).filter(EvaluationDate.group_id == group_id).all()
    )

    report_data = {
        'group': group.to_dict(),
        'students': [],
        'evaluation_dates': [d.to_dict() for d in eval_dates]
    }

    for student in group_members:
        student_data = student.to_dict()
        student_evaluations = [ev for ev in group_evaluations if ev.student_id == student.id]

        evaluations_by_date = {}
        for evaluation in student_evaluations:
            date_id = evaluation.evaluation_date_id
            evaluations_by_date[date_id] = evaluation.to_dict()

        student_data['evaluations'] = evaluations_by_date

        attitude_scores = [ev.attitude_score for ev in student_evaluations if ev.attitude_score is not None]
        skill_scores = [ev.skill_score for ev in student_evaluations if ev.skill_score is not None]
        cognition_scores = [ev.cognition_score for ev in student_evaluations if ev.cognition_score is not None]

        student_data['averages'] = {
            'attitude': sum(attitude_scores) / len(attitude_scores) if attitude_scores else None,
            'skill': sum(skill_scores) / len(skill_scores) if skill_scores else None,
            'cognition': sum(cognition_scores) / len(cognition_scores) if cognition_scores else None,
        }

        all_scores = attitude_scores + skill_scores + cognition_scores
        student_data['overall_average'] = sum(all_scores) / len(all_scores) if all_scores else None

        report_data['students'].append(student_data)

    return jsonify(report_data)


# Helper functions to keep import_spreadsheet small and readable

def _create_health_unit(name):
    health_unit = HealthUnit(name=name)
    db.session.add(health_unit)
    db.session.flush()
    return health_unit


def _create_preceptor(name):
    preceptor = Preceptor(name=name)
    db.session.add(preceptor)
    db.session.flush()
    return preceptor


def _create_group(name, period, year, semester, health_unit_id, preceptor_id):
    group = StudentGroup(
        name=name,
        period=period,
        year=year,
        semester=semester,
        health_unit_id=health_unit_id,
        preceptor_id=preceptor_id,
    )
    db.session.add(group)
    db.session.flush()
    return group


def _create_students_and_memberships(students_data, group_id):
    created = []
    for s in students_data:
        student = Student(name=s['name'])
        db.session.add(student)
        db.session.flush()
        membership = GroupMembership(student_id=student.id, group_id=group_id)
        db.session.add(membership)
        created.append(student)
    return created


def _create_eval_dates(date_strs, group_id):
    eval_dates = []
    for date_str in date_strs:
        eval_date = EvaluationDate(group_id=group_id, date=datetime.strptime(date_str, '%Y-%m-%d').date())
        db.session.add(eval_date)
        db.session.flush()
        eval_dates.append(eval_date)
    return eval_dates


def _create_evaluations_for_student(student_id, eval_dates, scores_list):
    for i, scores in enumerate(scores_list):
        evaluation = Evaluation(
            student_id=student_id,
            evaluation_date_id=eval_dates[i].id,
            attitude_score=scores['attitude'],
            skill_score=scores['skill'],
            cognition_score=scores['cognition'],
        )
        db.session.add(evaluation)


@evaluation_bp.route('/import-spreadsheet', methods=['POST'])
def import_spreadsheet():
    """Import example data from a spreadsheet into the database.

    This endpoint uses helper functions to reduce complexity and variable count.
    """
    try:
        health_unit = _create_health_unit("UNIDADE DE SAÚDE DA FAMÍLIA DO BOM TEMPO")
        preceptor = _create_preceptor("DR Renê Carvalho de Brito")

        group = _create_group(
            name="8ª ETAPA DO PIESF (Terças-feiras)",
            period="8ª ETAPA",
            year=2025,
            semester=1,
            health_unit_id=health_unit.id,
            preceptor_id=preceptor.id,
        )

        students_data = [
            {"name": "ISABELA PEREIRA"},
            {"name": "INGRID MACEDO"},
        ]

        created_students = _create_students_and_memberships(students_data, group.id)

        evaluation_dates_data = [
            "2025-02-11", "2025-02-25", "2025-03-18", "2025-04-01",
            "2025-04-15", "2025-04-29", "2025-05-13", "2025-05-27", "2025-06-10",
        ]

        eval_dates = _create_eval_dates(evaluation_dates_data, group.id)

        isabela_scores = [
            {"attitude": 10, "skill": 10, "cognition": 10},
            {"attitude": 10, "skill": 10, "cognition": 10},
            {"attitude": 10, "skill": 10, "cognition": 10},
            {"attitude": 10, "skill": 10, "cognition": 10},
            {"attitude": 10, "skill": 10, "cognition": 10},
            {"attitude": 7, "skill": 7, "cognition": 7},
            {"attitude": 10, "skill": 10, "cognition": 10},
            {"attitude": 10, "skill": 10, "cognition": 10},
            {"attitude": 7, "skill": 7, "cognition": 7},
        ]

        ingrid_scores = [
            {"attitude": 10, "skill": 10, "cognition": 10},
            {"attitude": 10, "skill": 10, "cognition": 10},
            {"attitude": 10, "skill": 10, "cognition": 10},
            {"attitude": 10, "skill": 10, "cognition": 10},
            {"attitude": 10, "skill": 10, "cognition": 10},
            {"attitude": 10, "skill": 10, "cognition": 10},
            {"attitude": 10, "skill": 10, "cognition": 10},
            {"attitude": 10, "skill": 10, "cognition": 10},
            {"attitude": 7, "skill": 7, "cognition": 7},
        ]

        _create_evaluations_for_student(created_students[0].id, eval_dates, isabela_scores)
        _create_evaluations_for_student(created_students[1].id, eval_dates, ingrid_scores)

        db.session.commit()

        return jsonify({"message": "Dados importados com sucesso!", "group_id": group.id}), 201

    except (SQLAlchemyError, ValueError) as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
