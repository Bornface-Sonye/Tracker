from .models import Payment
import requests
import base64
from datetime import datetime
from django.conf import settings

class SubscriptionManager:
    def __init__(self, student):
        self.student = student
        self.payment_info = Payment.objects.get(reg_no=self.student)

    def has_subscription(self):
        return self.payment_info.complaints_remaining > 0

    def decrement_complaint(self):
        if self.has_subscription():
            self.payment_info.complaints_remaining -= 1
            self.payment_info.save()
            return True
        return False

    def recharge_subscription(self, amount):
        self.payment_info.amount_available += amount
        self.payment_info.complaints_remaining += amount // 10  # Assuming Kshs 10 per complaint
        self.payment_info.save()

class PaymentProcessor:
    def __init__(self, phone_number, amount):
        self.phone_number = phone_number
        self.amount = amount
        self.pochi_phone_number = settings.POCHI_PHONE_NUMBER  # Pochi La Biashara phone number
        self.consumer_key = settings.CONSUMER_KEY
        self.consumer_secret = settings.CONSUMER_SECRET

    def get_access_token(self):
        api_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
        response = requests.get(api_url, auth=(self.consumer_key, self.consumer_secret))
        json_response = response.json()
        return json_response["access_token"]

    def initiate_payment(self):
        access_token = self.get_access_token()
        api_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        payload = {
            'BusinessShortCode': self.pochi_phone_number,  # Pochi La Biashara phone number
            'Password': base64.b64encode((self.pochi_phone_number + self.pochi_phone_number + datetime.now().strftime('%Y%m%d%H%M%S')).encode()).decode(),
            'Timestamp': datetime.now().strftime('%Y%m%d%H%M%S'),
            'TransactionType': 'CustomerPayBillOnline',  # Adjust as per your need
            'Amount': self.amount,
            'PartyA': self.phone_number,  # Customer's phone number
            'PartyB': self.pochi_phone_number,  # Pochi La Biashara phone number
            'PhoneNumber': self.phone_number,
            'CallBackURL': 'https://yourwebsite.com/callback',  # Your callback URL
            'AccountReference': self.phone_number,  # If you set `phone_number` when they enter it
            'TransactionDesc': 'Payment for complaints'
        }

        response = requests.post(api_url, json=payload, headers=headers)
        return response.json()
