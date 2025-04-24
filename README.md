# How to run it?

1. First install 2 python virtual environments or just one via:

   - On Linux:

     `simply run "./activate-env.sh"`

   - On Windows:

     `python -m venv/Your-Env-Name`

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
