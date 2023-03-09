from flask import (Blueprint, flash, get_flashed_messages, redirect,
                   render_template, request, url_for)
from flask_login import current_user, login_required
from sqlalchemy import not_

from . import db
from .auth import jwt_required
from .models import Departments, Projects, ProjectsDepartmentsIntermediary

departments_bp = Blueprint('departments', __name__, url_prefix='/departments')

@departments_bp.route('/', methods=['GET', 'POST'])
@jwt_required
@login_required
def list_departments():
    departments = Departments.query.all()

    if request.method == 'POST':
        department_name = request.form['department_name']
        # Check if department with same name already exists
        existing_department = Departments.query.filter_by(department_name=department_name).first()
        if existing_department:
            flash('Department already exists')
        else:
            new_department = Departments(department_name=department_name)
            db.session.add(new_department)
            db.session.commit()
            flash('Department created successfully')
        return redirect(url_for('departments.list_departments'))

    return render_template('departments.html', departments=departments)

@departments_bp.route('/<int:department_id>/delete', methods=['POST'])
@login_required
def delete_department(department_id):
    department = Departments.query.filter_by(id=department_id).first()
    if not department:
        flash('Department not found')
    else:
        db.session.delete(department)
        db.session.commit()
        flash('Department deleted successfully')
    return redirect(url_for('departments.list_departments', departments=Departments.query.all()))


@departments_bp.route('/<int:department_id>', methods=['GET', 'POST'])
@login_required
def department(department_id):
    department = Departments.query.filter_by(id=department_id).first()
    if not department:
        flash('Department not found')
        return redirect(url_for('departments.list_departments'))
    
    projects = db.session.query(Projects).join(ProjectsDepartmentsIntermediary).filter_by(department_id=department_id)
    
    if request.method == 'POST':
        department_name = request.form['department_name']
        existing_department = Departments.query.filter_by(department_name=department_name).first()
        if existing_department:
            flash('Department already exists')
        else:
            # Retrieve the updated department name from the hidden span element
            department_name = request.form.get('department_name_hidden')
            department.department_name = department_name
            db.session.commit()
            flash('Department updated successfully')
        return redirect(url_for('departments.department', department_id=department_id))

    assigned_project_ids = [project.id for project in projects]
    available_projects = Projects.query.filter(~Projects.departments.any(id=department_id)).filter(~Projects.id.in_(assigned_project_ids)).all()

    return render_template('department_view.html', department=department, projects=projects, available_projects=available_projects)

@departments_bp.route('/<int:department_id>/reassign_project/<int:project_id>', methods=['POST'])
@login_required
def reassign_project(department_id, project_id):
    department = Departments.query.filter_by(id=department_id).first()
    if not department:
        flash('Department not found')
        return redirect(url_for('departments.list_departments'))

    new_department_id = request.form['department_id']
    if not new_department_id:
        flash('Please choose a department to reassign the project to')
        return redirect(url_for('departments.department', department_id=department_id))

    project = Projects.query.get(project_id)
    if not project:
        flash('Project not found')
        return redirect(url_for('departments.department', department_id=department_id))

    new_department = Departments.query.get(new_department_id)
    if not new_department:
        flash('Department not found')
        return redirect(url_for('departments.department', department_id=department_id))

    intermediary = ProjectsDepartmentsIntermediary.query.filter_by(project=project, department=department).first()
    if not intermediary:
        flash('Project not assigned to this department')
    else:
        intermediary.department = new_department
        db.session.commit()
        flash('Project reassigned successfully')

    return redirect(url_for('departments.department', department_id=department_id))


@departments_bp.route('/<int:department_id>/remove_project/<int:project_id>', methods=['POST'])
@login_required
def remove_project(department_id, project_id):
    department = Departments.query.filter_by(id=department_id).first()
    if not department:
        flash('Department not found')
    else:
        project = Projects.query.get(project_id)
        if not project:
            flash('Project not found')
        else:
            intermediary = ProjectsDepartmentsIntermediary.query.filter_by(project=project, department=department).first()
            if not intermediary:
                flash('Project not assigned to this department')
            else:
                db.session.delete(intermediary)
                db.session.commit()
                flash('Project removed successfully')

    return redirect(url_for('departments.department', department_id=department_id))

@departments_bp.route('/<int:department_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_department(department_id):
    department = Departments.query.filter_by(id=department_id).first()
    if not department:
        flash('Department not found')
        return redirect(url_for('departments.list_departments'))

    if request.method == 'POST':
        department_name = request.form['department_name']
        existing_department = Departments.query.filter_by(department_name=department_name).first()
        if existing_department:
            flash('Department already exists')
        else:
            department.department_name = department_name
            db.session.commit()
            flash('Department updated successfully')
        return redirect(url_for('departments.list_departments'))

    return render_template('department_edit.html', department=department)



@departments_bp.route('/projects', methods=['GET', 'POST'])
@jwt_required
@login_required
def projects():
    search = request.args.get('search', '')
    department_id = request.args.get('department_id')
    projects_query = Projects.query.filter(Projects.project_name.ilike(f'%{search}%'))
    if department_id:
        projects_query = projects_query.filter(Projects.departments.any(Departments.id == department_id))
    projects = projects_query.all()

    if request.method == 'POST':
        project_name = request.form['project_name']
        project_description = request.form['project_description']
        department_ids = request.form.getlist('department_ids')
        project_picture = None

        if 'project_picture' in request.files:
            project_picture = request.files['project_picture']
            if project_picture.filename != '':
                project_picture.save('static/images/' + project_picture.filename)

        new_project = Projects(
            project_name=project_name,
            project_description=project_description,
            project_picture=project_picture.filename if project_picture else None
        )
        for department_id in department_ids:
            department = Departments.query.filter_by(id=department_id).first()
            intermediary = ProjectsDepartmentsIntermediary(project=new_project, department=department)
            new_project.departments.append(intermediary)
            db.session.add(intermediary) # Add intermediary to session

        db.session.add(new_project)
        db.session.commit()
        return redirect(url_for('departments.projects'))

    return render_template('projects.html', projects=projects, departments=Departments.query.all(), department_id=department_id)

@departments_bp.route('/assign_project', methods=['POST'])
@login_required
def assign_project():
    department_id = request.form['department_id']
    project_id = request.form['project_id']

    department = Departments.query.filter_by(id=department_id).first()
    if not department:
        flash('Department not found')
        return redirect(url_for('departments.projects'))

    project = Projects.query.get(project_id)
    if not project:
        flash('Project not found')
        return redirect(url_for('departments.projects'))

    intermediary = ProjectsDepartmentsIntermediary.query.filter_by(project=project, department=department).first()
    if intermediary:
        flash('Project already assigned to this department')
    else:
        intermediary = ProjectsDepartmentsIntermediary(project=project, department=department)
        project.departments.append(intermediary)
        db.session.add(intermediary)
        db.session.commit()
        flash('Project assigned successfully')

    return redirect(url_for('departments.projects'))


@departments_bp.route('/projects/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    project = Projects.query.filter_by(id=project_id).first()
    db.session.delete(project)
    db.session.commit()
    flash('Project deleted successfully')
    return redirect(url_for('departments.projects'))

@departments_bp.route('/projects/<int:project_id>/view', methods=['GET'])
@login_required
def view_project(project_id):
    project = Projects.query.get_or_404(project_id)
    return render_template('project.html', project=project)



@departments_bp.route('/projects/<int:project_id>', methods=['GET', 'POST'])
@login_required
def project(project_id):
    project = Projects.query.get_or_404(project_id)

    if request.method == 'POST':
        project_name = request.form['project_name']
        project_description = request.form['project_description']
        department_ids = request.form.getlist('department_ids')
        project_picture = None

        if 'project_picture' in request.files:
            project_picture = request.files['project_picture']
            if project_picture.filename != '':
                project_picture.save('static/images/' + project_picture.filename)

        project.project_name = project_name
        project.project_description = project_description
        project.project_picture = project_picture.filename if project_picture else None

        # Clear the existing departments
        intermediaries = ProjectsDepartmentsIntermediary.query.filter_by(project_id=project_id).all()
        for intermediary in intermediaries:
            db.session.delete(intermediary)

        # Assign the selected departments to the project
        for department_id in department_ids:
            department = Departments.query.filter_by(id=department_id).first()
            if department:
                intermediary = ProjectsDepartmentsIntermediary(project=project, department=department)
                project.departments.append(intermediary)

        db.session.commit()
        flash('Project updated successfully')
        return redirect(url_for('departments.projects'))

    departments = Departments.query.all()
    assigned_departments = [intermediary.department_id for intermediary in ProjectsDepartmentsIntermediary.query.filter_by(project_id=project_id).all()]

    return render_template('project.html', project=project, departments=departments, assigned_departments=assigned_departments)
