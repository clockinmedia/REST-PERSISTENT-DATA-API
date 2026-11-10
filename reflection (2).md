# Reflection: Clinical Records RESTful API with SQLite and JSON Lines

I built a Flask service that stores clinical records in two places. After creating a virtual environment and installing Flask, SQLAlchemy, and Pydantic, I defined a `ClinicalData` database model and Pydantic schemas for validation. I then implemented `POST /clinical/` to save a record to SQLite and append it to a JSON Lines file, and `GET /clinical/` to list every record. Finally, I tested both endpoints with curl and inspected `clinical_data.db` and `data/clinical_data.jsonl`.

I added three clinical columns: `blood_pressure`, `heart_rate`, and `allergies`. What surprised me was how much Pydantic does with little code; a pattern rule rejects a blood pressure like "high." I was also surprised that macOS uses port 5000 for AirPlay, so I moved the server to port 5001.

My code evolved to commit the database write only after the JSON line is written, keeping both stores consistent.

I now better understand how technical, semantic, and organizational interoperability fit together. I would like to learn more about database migrations and securing patient data.
