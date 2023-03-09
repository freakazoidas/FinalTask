import datetime

from flask import (Blueprint, flash, get_flashed_messages, redirect,
                   render_template, request, url_for)
from flask_login import current_user, login_required
from sqlalchemy import not_

from . import db
from .models import (PlantGroup, PlantGroupIntermediary, PlantGroupUsers,
                     PlantSingle, PlantWateringHistory, User)

plants_bp = Blueprint('plants', __name__, url_prefix='/plants')

@plants_bp.route('/plant_groups', methods=['GET', 'POST'])
@login_required
def plant_groups():
    if request.method == 'POST':
        # Create a new plant group and assign it to the logged in user
        new_group = PlantGroup(name=request.form.get('group_name'))
        db.session.add(new_group)
        new_group_user = PlantGroupUsers(user=current_user, plant_group=new_group)
        db.session.add(new_group_user)
        db.session.commit()
        flash('New plant group created!', 'success')

    # Get all plant groups assigned to the logged in user
    plant_groups = PlantGroup.query.join(PlantGroupUsers).filter(PlantGroupUsers.user_id == current_user.id).all()

    # Get all plant names assigned to each plant group
    plant_names = {}
    for group in plant_groups:
        intermediaries = PlantGroupIntermediary.query.filter_by(plant_group_id=group.id).all()
        plant_names[group.name] = [intermediary.plant.name for intermediary in intermediaries]

    return render_template('plant_groups.html', plant_groups=plant_groups, plant_names=plant_names)

@plants_bp.route('/assign_user/<int:group_id>', methods=['POST'])
@login_required
def assign_user(group_id):
    # Get the email and assigned group ID from the form submission
    email = request.form.get('user_email')
    assigned_group_id = request.form.get('assigned_group')

    # Check if the user with the given email address exists
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('User with the given email address does not exist.', 'error')
        return redirect(url_for('plants.plant_groups'))

    # Check if the user is already assigned to the given group
    existing_assignment = PlantGroupUsers.query.filter_by(user_id=user.id, plant_group_id=assigned_group_id).first()
    if existing_assignment:
        flash('User is already assigned to this group.', 'warning')
        return redirect(url_for('plants.plant_groups'))

    # Make sure the group the user is being assigned to belongs to the current user
    group_user = PlantGroupUsers.query.filter_by(user_id=current_user.id, plant_group_id=group_id).first()
    if not group_user:
        flash('Plant group not found.', 'error')
        return redirect(url_for('plants.plant_groups'))

    # Add the user to the group
    new_assignment = PlantGroupUsers(user=user, plant_group_id=assigned_group_id)
    db.session.add(new_assignment)
    db.session.commit()

    flash(f'{email} has been assigned to the group!', 'success')
    return redirect(url_for('plants.plant_groups'))


@plants_bp.route('/delete_group/<int:group_id>', methods=['POST'])
@login_required
def delete_group(group_id):
    # Find the plant group to delete
    group = PlantGroup.query.filter_by(id=group_id).first()

    # Make sure the group belongs to the current user
    if group and PlantGroupUsers.query.filter_by(user_id=current_user.id, plant_group_id=group.id).first():
        # Delete the group and any associated data
        PlantGroupIntermediary.query.filter_by(plant_group_id=group.id).delete()
        PlantGroupUsers.query.filter_by(plant_group_id=group.id).delete()
        PlantGroup.query.filter_by(id=group.id).delete()
        db.session.commit()
        flash('Plant group deleted!', 'success')

    return redirect(url_for('plants.plant_groups'))




@plants_bp.route('/plant_groups/<int:group_id>')
@login_required
def plant_group_single(group_id):
    # Get the plant group
    group = PlantGroup.query.filter_by(id=group_id).first()

    # Get all plants in the group assigned to the current user and their latest watering history
    user_plants = []
    plant_intermediaries = PlantGroupIntermediary.query.filter_by(plant_group_id=group_id).join(PlantSingle).all()

    for intermediary in plant_intermediaries:
        group_user = PlantGroupUsers.query.filter_by(user_id=current_user.id, plant_group_id=intermediary.plant_group_id).first()
        if group_user and group_user.plant_group == intermediary.plant_group:
            latest_history = PlantWateringHistory.query.filter_by(plant_id=intermediary.plant.id).order_by(PlantWateringHistory.date.desc()).first()
            last_watered = latest_history.date if latest_history else "No watering data"
            user_plants.append((intermediary, last_watered))

    current_date = datetime.datetime.now().date()

    return render_template('plant_group_single.html', group=group, plants=user_plants, current_date=current_date)

@plants_bp.route('/create_plant', methods=['GET', 'POST'])
@login_required
def create_plant():
    if request.method == 'POST':
        # Create a new plant and add it to the selected plant group assigned to the current user
        name = request.form.get('plant_name')
        type = request.form.get('plant_type')
        watering_frequency = request.form.get('watering_frequency')
        replanting_frequency = request.form.get('replanting_frequency')
        fertilizations_frequency = request.form.get('fertilization_frequency')
        group_id = request.form.get('group_id')

        new_plant = PlantSingle(
            name=name,
            type=type,
            watering_frequency=watering_frequency,
            replanting_frequency=replanting_frequency,
            fertilizations_frequency=fertilizations_frequency,
        )
        db.session.add(new_plant)

        # Add the new plant to the selected plant group assigned to the current user
        group_user = PlantGroupUsers.query.filter_by(user_id=current_user.id, plant_group_id=group_id).first()
        new_intermediary = PlantGroupIntermediary(
            plant_group=group_user.plant_group,
            plant=new_plant,
        )
        db.session.add(new_intermediary)

        db.session.commit()
        flash('New plant created!', 'success')
        return redirect(url_for('plants.plant_groups'))

    # Get all plant groups assigned to the logged in user
    plant_groups = PlantGroup.query.join(PlantGroupUsers).filter(
        PlantGroupUsers.user_id == current_user.id
    ).all()

    return render_template('plant_create.html', plant_groups=plant_groups)



@plants_bp.route('/update_plant', methods=['POST'])
@login_required
def update_plant():
    """
    Updates the watering history of a plant and adds a new entry to PlantWateringHistory.
    """
    plant_id = request.form.get('plant_id')
    comment = request.form.get('comment')
    watering_date = datetime.datetime.strptime(request.form.get('watering_date'), '%Y-%m-%d').date()

    # Find the plant and make sure it belongs to the current user
    plant = PlantSingle.query.filter_by(id=plant_id).first()
    group_users = PlantGroupUsers.query.filter_by(user_id=current_user.id).all()
    if plant and any(intermediary.plant_group_id in [group_user.plant_group_id for group_user in group_users] for intermediary in plant.group_intermediaries):
        # Update the plant's last watering date and add a new entry to PlantWateringHistory
        plant.last_watered = watering_date
        db.session.add(PlantWateringHistory(plant=plant, date=watering_date, comment=comment))
        db.session.commit()
        flash('Plant watering history updated!', 'success')

    return redirect(url_for('plants.plant_group_single', group_id=plant.group_intermediaries[0].plant_group_id))

@plants_bp.route('/plant_single_edit/<int:plant_id>', methods=['GET', 'POST'])
@login_required
def plant_single_edit(plant_id):
    # Get all plant groups assigned to the logged in user
    plant_groups = PlantGroup.query.join(PlantGroupUsers).filter(
        PlantGroupUsers.user_id == current_user.id
    ).all()

    # Get the plant being edited
    plant = PlantSingle.query.filter_by(id=plant_id).first()

    # Make sure the plant belongs to the current user
    group_users = PlantGroupUsers.query.filter_by(user_id=current_user.id).all()
    if not plant or not any(
        intermediary.plant_group_id in [group_user.plant_group_id for group_user in group_users]
        for intermediary in plant.group_intermediaries
    ):
        flash('Plant not found.', 'error')
        return redirect(url_for('plants.plant_groups'))

    if request.method == 'POST':
        # Update the plant with the new information
        plant.name = request.form.get('plant_name')
        plant.type = request.form.get('plant_type')
        plant.watering_frequency = request.form.get('watering_frequency')
        plant.replanting_frequency = request.form.get('replanting_frequency')
        plant.fertilizations_frequency = request.form.get('fertilization_frequency')
        db.session.commit()
        flash('Plant updated!', 'success')

    # Get the IDs of the plant groups the plant belongs to
    group_ids = [intermediary.plant_group_id for intermediary in plant.group_intermediaries]

    # Pass the plant and plant group information to the template
    return render_template(
        'plant_single_edit.html',
        plant=plant,
        plant_id=plant_id,
        groups=plant_groups,
        group_ids=group_ids,
    )


@plants_bp.route('/delete_plant/<int:plant_id>', methods=['POST'])
@login_required
def delete_plant(plant_id):
    # Find the plant and make sure it belongs to the current user
    plant = PlantSingle.query.filter_by(id=plant_id).first()
    group_users = PlantGroupUsers.query.filter_by(user_id=current_user.id).all()
    if plant and any(intermediary.plant_group_id in [group_user.plant_group_id for group_user in group_users] for intermediary in plant.group_intermediaries):
        # Delete the plant and any associated data
        PlantGroupIntermediary.query.filter_by(plant_id=plant.id).delete()
        PlantWateringHistory.query.filter_by(plant_id=plant.id).delete()
        PlantSingle.query.filter_by(id=plant.id).delete()
        db.session.commit()
        flash('Plant deleted!', 'success')

    return redirect(url_for('plants.plant_groups'))

@plants_bp.route('/clear_last_entry/<int:plant_id>', methods=['DELETE'])
@login_required
def clear_last_entry(plant_id):
    # Find the plant and make sure it belongs to the current user
    plant = PlantSingle.query.filter_by(id=plant_id).first()
    group_users = PlantGroupUsers.query.filter_by(user_id=current_user.id).all()
    if plant and any(
        intermediary.plant_group_id in [group_user.plant_group_id for group_user in group_users]
        for intermediary in plant.group_intermediaries
    ):
        # Delete the last watering history entry for the plant
        last_entry = PlantWateringHistory.query.filter_by(plant_id=plant_id).order_by(PlantWateringHistory.date.desc()).first()
        if last_entry:
            db.session.delete(last_entry)
            db.session.commit()
            flash('Last watering history entry deleted!', 'success')

    return redirect(url_for('plants.plant_single_edit', plant_id=plant_id))
