# CAQM
CAQM is a software engineering course project designed to simplifiy and speed up clinic operations by efficiently scheduling appointments and managing waiting lists. The system allows patients, doctors, and administrators to interact seamlessly through a single platform. 
The project applies object-oriented design principles and follow software engineering best practices, with clear component separation (Authentication, Patient, Doctor, Admin, Appointment, Queue, and Notification).

## The CAQM system is divided into several components:
Authentication: Secure login and registration for all users.
Patient Module: Appointment booking, viewing queues, and receiving notifications.
Doctor Module: Managing patient queues and viewing appointment details.
Admin Module: Overseeing the system, managing users, and maintaining records.
Appointment: Managing scheduling.
Queue: keep traking the queue status and informe the patient of changes. 
Notification: Sends reminders and updates to users.

## to run the program you have to ensure that you have the following installed:
* [python 3.10](https://www.python.org/)
* [pip](https://pypi.org/project/pip/)

## Build Setup:

### 1. clone the repository:
git clone https://github.com/Mouaz-Ahmed-Alazazy/CAQM/
cd CAQM

### 2. create a virtual environment:
python -m venv .venv

### 3. activate the virtual environment:
.venv\Scripts\Activate.ps1

### 4. install the requirements:
pip install -r requirements.txt

## Test:
to verify that everything works run:
python manage.py test

## Run the Program:
### 1. Apply migrations:
python manage.py migrate

### 2. Run the server:
python manage.py runserver

### 3. To access the system click on the link http://127.0.0.1:8000/
