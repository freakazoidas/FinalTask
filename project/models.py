from flask_login import UserMixin
from sqlalchemy import Column, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from werkzeug.security import check_password_hash, generate_password_hash

from . import db


class User(UserMixin, db.Model):
    id = Column(Integer, primary_key=True)
    email = Column(String(100), unique=True)
    password = Column(String(100))
    name = Column(String(1000))

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class BillGroups(db.Model):
    __tablename__ = 'bill_groups'
    id = Column(Integer, primary_key=True)
    group_name = Column(String(255), unique=True)
    bill_intermediaries = relationship("BillGroupIntermediary", back_populates="bill_groups")

class BillGroupIntermediary(db.Model):
    __tablename__ = 'group_user_intermediary'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    group_id = Column(Integer, ForeignKey('bill_groups.id'))
    user = relationship("User")
    bill_groups = relationship("BillGroups", back_populates="bill_intermediaries")

class IndividualBill(db.Model):
    __tablename__ = 'individual_bill'
    id = Column(Integer, primary_key=True)
    bill_id = Column(Integer, ForeignKey('bill_groups.id'))
    bill_item = Column(String(255))
    item_price = Column(Numeric(100, 2))

class Projects(db.Model):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)
    project_name = Column(String(255), nullable=False)
    project_description = Column(String(1000), nullable=False)
    project_picture = Column(String(1000), nullable=True)
    departments = relationship("ProjectsDepartmentsIntermediary", back_populates="project", cascade="all, delete-orphan")
    def has_department(self, department_id):
        return ProjectsDepartmentsIntermediary.query.filter_by(project_id=self.id, department_id=department_id).first() is not None

class Departments(db.Model):
    __tablename__ = 'departments'
    id = Column(Integer, primary_key=True)
    department_name = Column(String(255), nullable=False, unique=True)
    projects = relationship("ProjectsDepartmentsIntermediary", back_populates="department", cascade="all, delete-orphan")

class ProjectsDepartmentsIntermediary(db.Model):
    __tablename__ = 'projects_departments_intermediary'
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    department_id = Column(Integer, ForeignKey('departments.id'))
    project = relationship("Projects", back_populates="departments")
    department = relationship("Departments", back_populates="projects")

class PlantSingle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(255))
    picture = db.Column(db.String(1000))
    watering_frequency = db.Column(db.Integer, nullable=False)
    replanting_frequency = db.Column(db.Integer)
    fertilizations_frequency = db.Column(db.Integer)

class PlantWateringHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant_single.id'))
    date = db.Column(db.Date, nullable=False)
    comment = db.Column(db.String(1000))
    plant = db.relationship('PlantSingle', backref=db.backref('watering_history', lazy=True))

class PlantGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)

class PlantGroupIntermediary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plant_group_id = db.Column(db.Integer, db.ForeignKey('plant_group.id'), nullable=False)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant_single.id'), nullable=False)
    plant_group = db.relationship('PlantGroup', backref=db.backref('plant_intermediaries', lazy=True))
    plant = db.relationship('PlantSingle', backref=db.backref('group_intermediaries', lazy=True))

class PlantGroupUsers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plant_group_id = db.Column(db.Integer, db.ForeignKey('plant_group.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('group_users', lazy=True))
    plant_group = db.relationship('PlantGroup', backref=db.backref('group_users', lazy=True), single_parent=True, cascade='all, delete-orphan')
