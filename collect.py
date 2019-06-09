from data import get_data

api = get_data(user_id=300870231,
               depth=2)
api.collect()
