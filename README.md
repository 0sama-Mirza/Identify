# How to run it?

1. First install 2 python virtual environments or just one via:

   - On Linux:

     `simply run "./activate-env.sh"`

   - On Windows:

     `python -m venv Your-Env-Name`

2. Name the first one Flask and the second one Fastapi or whatever
3. Activate the both environments in 2 separate terminals by:

   - On Linux:

     `simply run the "./activate-env.sh" file`

   - On Windows:

     `.\venv-name\Scripts\activate`

4. Install the requirements.txt for both of them via:

   `pip install -r requirements.txt`

5. To run the website run this command in Flask env:

   `python run.py`

   - This will run on http://127.0.0.1:5000/

6. To run the schedular for uploading the unsorted event files run:

   `uvicorn main:app --reload`

   - This will run on http://127.0.0.1:8000/



## Front-Back-End (flask-env)
```
pip install Flask Flask-Session Flask-APScheduler requests numpy gunicorn
python run.py # for development

gunicorn -w 4 -b 0.0.0.0:5000 run:app
waitress-serve --host=0.0.0.0 --port=5000 run:app // For Windows pip install waitress
python scheduler.py
```
## FDRP (Face Detection and Recognition Pipeline)
### 1st environment (fast-api)
```
pip install -r requirements.txt
uvicorn main:app --reload
```
### 2nd environment (deepface-env)
```
pip install opencv-python deepface tf-keras
python face_processing_manager.py
```
# How to run it?

1. First install 2 python virtual environments or just one via:

   - On Linux:

     `simply run "./activate-env.sh"`

   - On Windows:

     `python -m venv Your-Env-Name`

2. Name the first one Flask and the second one Fastapi or whatever
3. Activate the both environments in 2 separate terminals by:

   - On Linux:

     `simply run the "./activate-env.sh" file`

   - On Windows:

     `.\venv-name\Scripts\activate`

4. Install the requirements.txt for both of them via:

   `pip install -r requirements.txt`

5. To run the website run this command in Flask env:

   `python run.py`

   - This will run on http://127.0.0.1:5000/

6. To run the schedular for uploading the unsorted event files run:

   `uvicorn main:app --reload`

   - This will run on http://127.0.0.1:8000/



## Front-Back-End (flask-env)
```
pip install Flask Flask-Session Flask-APScheduler requests numpy
python run.py
```
## FDRP (Face Detection and Recognition Pipeline)
### 1st environment (fast-api)
```
pip install -r requirements.txt
uvicorn main:app --reload
```
### 2nd environment (deepface-env)
```
pip install opencv-python deepface tf-keras
python face_processing_manager.py
```

#### How to check end point of Identify:
```
curl -X POST http://localhost:8000/match-face/   -F "file=@/home/archmax/startup/FYP-Project/Identify/Front-Back-End/uploads/event_10/original_images/Imj81.JPG"   -F "user_id=1"   -F "event_id=11"
```