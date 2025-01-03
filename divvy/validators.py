# validators.py

from .models import User

def validate_exp_type(exp_type):
    if exp_type not in ["EQUAL", "EXACT", "PERCENT"]:
        raise ValueError("Invalid expense type. Valid types are EQUAL, EXACT, PERCENT.")

def validate_desc(desc):
    if not desc or len(desc) < 5:
        raise ValueError("Description must be at least 5 characters long.")

def validate_total_amt(amount):
    if amount <= 0:
        raise ValueError("Total amount must be greater than 0.")

def validate_user_ids(user_ids, valid_ids):
    if not all(int(uid) in valid_ids for uid in user_ids):
        raise ValueError("Invalid user ID in PaidBy or OwedBy.")

def validate_total(user_ids, amount):
    total = sum(user_ids.values())
    if total != amount:
        raise ValueError(f"Total amount mismatch. Expected {amount}, but got {total}.")

def validate_created_by(created_by_id, valid_ids):
    if created_by_id not in valid_ids:
        raise ValueError("Created By ID is not valid.")
