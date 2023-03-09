from flask import Blueprint, render_template, request
from flask_login import current_user, login_required

from project.models import BillGroupIntermediary, BillGroups, IndividualBill

from . import db

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name)

@main.route('/groups', methods=['GET', 'POST'])
@login_required
def groups():
    user_id = current_user.id
    user_groups = BillGroupIntermediary.query.filter_by(user_id=user_id).all()
    user_group_ids = [group.group_id for group in user_groups]
    groups = BillGroups.query.all()

    if request.method == 'POST':
        group_name = request.form['group_name']
        new_group = BillGroups(group_name=group_name)
        db.session.add(new_group)
        db.session.commit()
        # Create a new entry in the group_user_intermediary table to link the new group to the current user
        group_intermediary = BillGroupIntermediary(user_id=current_user.id, group_id=new_group.id)
        db.session.add(group_intermediary)
        db.session.commit()

    return render_template('groups.html', groups=groups, user_group_ids=user_group_ids, name=current_user.name)


from flask import redirect, url_for


@main.route('/groups/<int:bill_id>', methods=['GET', 'POST'])
@login_required
def bill(bill_id):
    bill_group = BillGroups.query.filter_by(id=bill_id).first()
    bill_items = IndividualBill.query.filter_by(bill_id=bill_id).all()
    if request.method == 'POST':
        bill_item = request.form['bill_item']
        item_price = request.form['item_price']
        new_bill = IndividualBill(bill_id=bill_id, bill_item=bill_item, item_price=item_price)
        db.session.add(new_bill)
        db.session.commit()
        return redirect(url_for('main.bill', bill_id=bill_id))
    return render_template('bill.html', bill_group=bill_group, bill_items=bill_items, name=current_user.name)
