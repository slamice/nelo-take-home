curl -X POST "http://127.0.0.1:8000/book_restaurant/" \
-H "Content-Type: application/json" \
-d '{
    "start_time": "2024-08-24T19:00:00",
    "diner_ids": [1, 2, 3],
    "restaurant_id": 2
}'