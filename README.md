# Instructions to run

We will need `python` and `poetry`. I have it set up with [asdf](https://asdf-vm.com/), but you can setup your python environment differently.
```
poetry install
```

First populate data. It's stored in a few csvs. Se are using sqlite for a database.

```
python3 populate_db.py
```

Start the server, it's in fast api:

```
fastapi dev main.py
```

Now we can run our queries:

Find a reservation given some diners:
```
curl -X POST "http://127.0.0.1:8000/find_reservation/" \
-H "Content-Type: application/json" \
-d '{
    "start_time": "2024-08-24T17:00:00",
    "diner_ids": [1, 2, 3]
}'
```

Book a restaurant from the previous endpoint:
```
curl -X POST "http://127.0.0.1:8000/book_restaurant/" \
-H "Content-Type: application/json" \
-d '{
    "start_time": "2024-08-24T19:00:00",
    "diner_ids": [1, 2, 3],
    "restaurant_id": 1
}'
```

Delete a reservation:
```
curl -X DELETE "http://127.0.0.1:8000/reservation/1" -H "Content-Type: application/json"
```

These script examples also exist in the **scripts** folder.

FastApi automatically generates docs [here](http://localhost:8000/docs)

**Notes:**
- I'd like to do some clean up for the test classes and session creating
- There is some more cleanup for basic things (linting using `ruff`, better logging)
- An agreement on the API contract would be nice to make more 
