"""
Created on 2024-05-02
by Divyesh Ranpariya (handle: divyesh599)
"""


from django.http import HttpResponse
from .models import User, Expense, ExpensePaidBy, ExpenseOwedBy
from .serializers import (
    UserSerializer,
    ExpenseSerializer,
    ExpensePaidBySerializer,
    ExpenseOwedBySerializer,
)

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import generics, status

from django.db import IntegrityError
from django.db.models import Sum
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .validators import validate_exp_type, validate_desc, validate_total_amt, validate_user_ids, validate_total, validate_created_by


def register_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, '/home/wac/Downloads/splitwise/splitwise/templates/register.html', {'form': form})


@login_required
def user_profile(request):
    return render(request, 'profile.html')


# Create your views here.
def homePage(request):
    # return HttpResponse("Welcome to my Django Project")
    return render(request, "index.html")


def allUser(request):
    data = User.objects.all().values()
    return HttpResponse(data)


class UserListCreateAPIView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


def validate_exp_type(exp_type):
    if exp_type not in ["EQUAL", "EXACT", "PERCENT"]:
        raise ValueError("Expense type must be one of: EQUAL, EXACT, PERCENT.")


def validate_desc(desc):
    if not isinstance(desc, str):
        raise ValueError("Description must be a string.")


def validate_total_amt(amt):
    if not isinstance(amt, int):
        raise ValueError("Total amount must be an integer.")


# def validate_user_ids(user_ids, user_id_list, field_name):
#     for uid, amt in user_ids.items():
#         if int(uid) not in user_id_list:
#             raise ValueError(f"Invalid user ID '{uid}' in '{field_name}'.")
#         if not isinstance(amt, (int, float)):
#             raise ValueError("Amount must be a number.")

def validate_user_ids(user_ids, uid_list):
    if user_ids is None:
        raise ValueError("User IDs cannot be None")
    for user_id, value in user_ids.items():
        if int(user_id) not in uid_list:
            raise ValueError(f"Invalid user ID '{user_id}'.")


def validate_total(total_dict, expected_total):
    if sum(total_dict.values()) != expected_total:
        raise ValueError(
            f"Total amount does not match the specified total amount of {expected_total}."
        )


def validate_created_by(created_by_id, user_id_list):
    if created_by_id not in user_id_list:
        raise ValueError(f"Invalid created by user ID '{created_by_id}'.")



@api_view(["POST"])
def add_expense(request):
    # Extract data from the request
    data = request.data

    paid_by = data.get('paidBy')
    owed_by = data.get('owedBy')
    created_by_id = data.get('created_by')

    exp_type = data.get("expense_type")
    desc = data.get("desc")
    amt = data.get("total_amount")

    # Validation checks for paid_by and owed_by
    if not paid_by or not owed_by:
        return Response({'error': 'Paid By and Owed By cannot be None'}, status=400)

    if created_by_id is None:
        return Response({'error': 'Created By cannot be None'}, status=400)

    # Get list of user IDs from the database
    uid_list = list(User.objects.values_list("userId", flat=True))

    # Define validation functions
    def validate_input():
        validate_exp_type(exp_type)
        validate_desc(desc)
        validate_total_amt(amt)

        print("Paid By:", paid_by)
        print("Owed By:", owed_by)

        # Validate user IDs in paid_by and owed_by
        validate_user_ids(paid_by, uid_list)
        validate_user_ids(owed_by, uid_list)

        # Validate totals based on expense type
        validate_total(paid_by, amt)
        if exp_type == "EQUAL":
            validate_total(owed_by, 0)
        elif exp_type == "EXACT":
            validate_total(owed_by, amt)
        elif exp_type == "PERCENT":
            validate_total(owed_by, 100)
        
        # Validate created_by_id
        validate_created_by(created_by_id, uid_list)

        # Check maximum number of participants
        if len(paid_by) > 1000 or len(owed_by) > 1000:
            raise ValueError("The maximum number of participants for an expense is 1000.")

        # Check maximum amount for an expense
        if amt > 100000000:
            raise ValueError("The maximum amount for an expense is INR 1,00,00,000.")

    # Validate input data
    try:
        validate_input()
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # Create and save the new expense object
    expense = Expense.objects.create(
        desc=desc, amount=amt, createdById_id=created_by_id
    )
    expense_id = expense.expenseId

    # Create ExpensePaidBy objects for each user who paid
    exp_paid = [
        ExpensePaidBy(
            expenseId_id=expense_id,
            userId_id=int(uid),
            amount=round(val, 2)
        )
        for uid, val in paid_by.items()
    ]
    
    # Bulk create ExpensePaidBy records
    ExpensePaidBy.objects.bulk_create(exp_paid)

    # Create ExpenseOwedBy objects based on expense type
    exp_owed = []
    if exp_type == "EQUAL":
        # Calculate equal amount owed by each user
        val = round(amt / len(uid_list), 2)
        thresh = amt - val * len(uid_list)
        exp_owed = [
            ExpenseOwedBy(
                expenseId_id=expense_id,
                userId_id=int(uid),
                amount=val + thresh if i == 0 else val,
            )
            for i, uid in enumerate(uid_list)
        ]
    elif exp_type == "EXACT":
        # Create ExpenseOwedBy objects with exact amounts owed
        exp_owed = [
            ExpenseOwedBy(
                expenseId_id=expense_id,
                userId_id=int(uid),
                amount=round(val, 2)
            )
            for uid, val in owed_by.items()
        ]
    elif exp_type == "PERCENT":
        # Create ExpenseOwedBy objects with amounts calculated based on percentage
        exp_owed = [
            ExpenseOwedBy(
                expenseId_id=expense_id,
                userId_id=int(uid),
                amount=round((amt * val) / 100, 2),
            )
            for uid, val in owed_by.items()
        ]

    # Bulk create ExpenseOwedBy records
    ExpenseOwedBy.objects.bulk_create(exp_owed)

    # Return success response
    return Response(
        {"message": f"Expense successfully added, EID : {expense_id}"},
        status=status.HTTP_201_CREATED,
    )

@api_view(["GET"])
def show_expenses(request, user_id=None):
    if user_id:
        # Get all expenses for the specified user
        user_expenses = Expense.objects.all()
        total_paid = (
            ExpensePaidBy.objects.filter(userId_id=user_id).aggregate(
                total_paid=Sum("amount")
            )["total_paid"]
            or 0
        )
        total_owed = (
            ExpenseOwedBy.objects.filter(userId_id=user_id).aggregate(
                total_owed=Sum("amount")
            )["total_owed"]
            or 0
        )
        total_balance = total_paid - total_owed

        expenses_data = []
        for expense in user_expenses:
            paid_amount = (
                ExpensePaidBy.objects.filter(
                    expenseId_id=expense.expenseId, userId_id=user_id
                ).aggregate(paid_amount=Sum("amount"))["paid_amount"]
                or 0
            )
            owed_amount = (
                ExpenseOwedBy.objects.filter(
                    expenseId_id=expense.expenseId, userId_id=user_id
                ).aggregate(owed_amount=Sum("amount"))["owed_amount"]
                or 0
            )
            balance = paid_amount - owed_amount

            expense_info = {
                "expense_id": expense.expenseId,
                "description": expense.desc,
                "amount": expense.amount,
                "paid_by_user": paid_amount,
                "owed_by_user": owed_amount,
                "balance": balance,
            }
            expenses_data.append(expense_info)

        user_expense_info = {
            "total_paid": total_paid,
            "total_owed": total_owed,
            "total_balance": total_balance,
            "expenses": expenses_data,
        }

        return Response(user_expense_info)
    else:
        # Get balances for everyone
        users = User.objects.all()
        balances = {}
        for user in users:
            expenses_paid = (
                ExpensePaidBy.objects.filter(userId_id=user.userId).aggregate(
                    total_paid=Sum("amount")
                )["total_paid"]
                or 0
            )
            expenses_owed = (
                ExpenseOwedBy.objects.filter(userId_id=user.userId).aggregate(
                    total_owed=Sum("amount")
                )["total_owed"]
                or 0
            )
            balance = expenses_paid - expenses_owed
            balances[user.name] = balance
        return Response(balances)


@api_view(['POST'])
def add_user(request):
    # Extract data from the request
    name = request.data.get('name')
    email = request.data.get('email')
    mobile_number = request.data.get('mobileNumber')

    try:
        # Validate input data
        if not name:
            raise ValueError("Name field is required.")

        # Check if the email is valid
        try:
            validate_email(email)
        except ValidationError:
            raise ValueError("Invalid email format.")

        # Check if the mobile number is valid
        if not str(mobile_number).isdigit() or len(str(mobile_number)) != 10:
            raise ValueError("Invalid mobile number format.")

        # Create and save the new user object
        new_user = User.objects.create(
            name=name, email=email, mobileNumber=mobile_number
        )

        # Construct response data
        response_data = {
            'message': 'User added successfully',
            'user_id': new_user.userId,
            'name': new_user.name,
            'email': new_user.email,
            'mobileNumber': new_user.mobileNumber
        }

        # Return JSON response with success message and user details
        return Response(response_data, status=status.HTTP_201_CREATED)

    except ValueError as e:
        # Return error response if validation fails
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    except IntegrityError:
        # Return error response if the email already exists
        return Response({'error': 'Email address already exists.'}, status=status.HTTP_400_BAD_REQUEST)
