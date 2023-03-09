# Plant App

## How to Run

To run the app locally, follow these steps:

1. Create a virtual environment: `python3 -m venv auth`
2. Activate the virtual environment:
   - For Windows: `. auth/Scripts/activate`
   - For Ubuntu: `. auth/bin/activate`
3. Install the requirements: `pip install -r requirements.txt`
4. Set the `FLASK_APP` environment variable: `export FLASK_APP=project`
5. Run the app: `flask run`
6. (Optional) Update the `requirements.txt` file with any new packages: `pip freeze > requirements.txt`

## Flask DB Migration

To perform a Flask database migration, follow these steps:

1. Make sure the Flask-Migrate package is installed: pip install Flask-Migrate
2. Create a migration repository: flask db init
3. Create a migration script: flask db migrate -m "migration message"
4. Upgrade the database: flask db upgrade
5. To downgrade the database, run flask db downgrade with the name of the revision to downgrade to.

## Credentials

You can use these credentials to test:

- Email: asas@gmail.com
- Password: asasas

## Groups Database

![image](https://i.imgur.com/C1xxeJH.png)

## Styles Used

- CSS Bulma
- CSS Bootstrap

## Technologies Used

- JWT token
- SQLAlchemy
- Werkzeug
- Jinja2

## Plant App

### Features

- Create, delete, and edit plant groups
- Assign plant groups to friends to share and track plants
- Add, remove, and edit plants and their characteristics
- Upload pictures for plants (not currently viewable)
- Track the watering history of individual plants
- Remove last watering entry if entered accidentally
- Pre-select today's date when watering plants, but select a custom date in the calendar

## Department Project Management App

### Features

- Create, delete, and edit departments
- Create, delete, and edit projects
- Assign projects to departments and vice versa
- Prepopulate information if the project is already assigned to a department and vice versa

## Bill Split App

### Features

- Enter expenses and split them among friends
