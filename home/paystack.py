import requests
from django.conf import settings

class Paystack:
    @staticmethod
    def verify_payment(reference, amount):
        url = f"https://api.paystack.co/transaction/verify/{reference}"
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            res_data = response.json()
            if res_data['data']['status'] == 'success':
                paid_amount = res_data['data']['amount'] / 100  # Convert from kobo to naira/cedis
                return float(paid_amount) == float(amount)
        return False
