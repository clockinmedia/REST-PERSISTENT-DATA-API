# Clinical Records RESTful API (SQLite + JSON Lines)

A Flask service that stores clinical records in two places:

- **SQLite** (`clinical_data.db`) for transactional integrity
- **JSON Lines** (`data/clinical_data.jsonl`) as an append-only audit trail

Pydantic schemas validate every record before it is saved.

## Added columns

| Column | Type | Validation |
|---|---|---|
| `blood_pressure` | text | Must look like `120/80` |
| `heart_rate` | integer | 20–250 bpm |
| `allergies` | text | Optional, defaults to `"None"` |

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

The server runs at `http://127.0.0.1:5001`. It uses port 5001 because macOS AirPlay Receiver often uses port 5000.

## Test with curl (in a second Terminal window)

Add a record:

```bash
curl -X POST http://127.0.0.1:5001/clinical/ \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"P001","patient_name":"Jane Doe","age":45,"diagnosis":"Hypertension","blood_pressure":"140/90","heart_rate":78,"allergies":"Penicillin"}'
```

List all records:

```bash
curl http://127.0.0.1:5001/clinical/
```

Invalid data is rejected with `422`:

```bash
curl -X POST http://127.0.0.1:5001/clinical/ \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"P003","patient_name":"Bad Data","age":30,"diagnosis":"Test","blood_pressure":"high","heart_rate":5}'
```

## Verify persistence

```bash
sqlite3 clinical_data.db "SELECT * FROM clinical_data;"
cat data/clinical_data.jsonl
```
