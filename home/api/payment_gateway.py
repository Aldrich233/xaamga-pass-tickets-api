from smtplib import SMTPException
from django.conf import settings
import json
import os
import uuid
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.openapi import AutoSchema
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError, PermissionDenied, NotAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response 
from rest_framework import status
from django.shortcuts import render , reverse ,  redirect
from home.models import CustomUser, ETicket, EndUserDetail, Event, EventPassCategory, MyCart, Order, Ticket
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ValidationError
from django.shortcuts import  get_object_or_404
from rest_framework.authtoken.models import Token
from django.core.mail import send_mail, EmailMessage
import time
import stripe

STRIPE_WEBHOOK_SECRET = "whsec_aee52ec1cbc7143659007e3aee8028044256761930315b877c8b5ae869f8f920"
# STRIPE_WEBHOOK_SECRET = "whsec_aee52ec1cbc7143659007e3aee8028044256761930315b877c8b5ae869f8f920"



class StripeGroupPaymentAPIView(APIView):
    schema = AutoSchema()

    def post(self, request):
        # Récupérer l'utilisateur et la commande
        user_id = request.data.get('user_id')
        order_id = request.data.get('order_id')
        # order_id = request.data.get('order_id')

        if not user_id or not order_id:
            return Response({"error": "Missing 'user_id' or 'order_id' in request data"},
                            status=status.HTTP_400_BAD_REQUEST)

        #  Étape 1 : Récupérer l'instance de CustomUser
        user_instance = get_object_or_404(CustomUser, id=user_id)

        #  Étape 2 : Récupérer EndUserDetail en utilisant l'instance
        user_detail = get_object_or_404(EndUserDetail, user=user_instance)

        #  Étape 3 : Récupérer la commande
        order = get_object_or_404(Order, order_id=order_id, user=user_instance)

        # Vérifier si la commande existe et récupérer le montant total
        events_amount = order.total_amount
        if not events_amount:
            return Response({"error": "Order has no total amount"}, status=status.HTTP_400_BAD_REQUEST)

        # Récupérer les informations de l'utilisateur pour le paiement
        customer_name = user_detail.first_name
        customer_surname = user_detail.second_name
        customer_number = user_detail.telephone_number
        customer_birthday = "1998-05-20"  # Exemple de valeur
        customer_location = user_detail.address

        url = reverse('payment-response', kwargs={'user_id': user_id})
        success_url = "http://localhost:4200/success"
        # success_url = "http://localhost:4200/success"
        # success_url = request.build_absolute_uri(url)
        print(success_url)
        cancel_url = "http://localhost:4200/cancel"
        # cancel_url = "http://localhost:4200/cancel"
        # cancel_url = request.build_absolute_uri(reverse('payment-cancel'))

        missing_fields = []

        # Vérifier les champs obligatoires
        if not customer_name:
            missing_fields.append("first_name")
        if not customer_surname:
            missing_fields.append("second_name")
        if not customer_number:
            missing_fields.append("telephone_number")
        if not customer_location:
            missing_fields.append("address")

        if missing_fields:
            return Response({"error": "Required user fields are missing", "missing_fields": missing_fields},
                            status=status.HTTP_400_BAD_REQUEST)

        # Préparer les données de paiement
        payload = {
            "customer_name": customer_name,
            "customer_surname": customer_surname,
            "customer_number": customer_number,
            "customer_birthday": customer_birthday,
            "customer_location": customer_location,
            "cancel_url": cancel_url,
            "success_url": success_url,
            "order_id": order.order_id,  # Utilisation de l'order_id de la commande
            "events_amount": float(order.total_amount)
        }


        print(payload)
        headers = {
            'X-API-Key': '81bdf51c909897d5cb7755ab880fe52e',
            'Content-Type': 'application/json'
        }

        url = 'https://www.xaamga-cashless.tv/paywall/api/stripe/groupPayment/'

        try:
            # Faire la requête Stripe
            response = requests.post(url, json=[payload], headers=headers,timeout=30)
            print(response.status_code)
            print(response.text)

            if response.status_code == 200:
                response_text = response.text
                response_data = json.loads(response_text.replace('\\"', '"'))

                if isinstance(response_data, list) and len(response_data) > 0:
                    callback = response_data[0].get('callback', {})
                    payment_url = callback.get('payment_url')
                    payment_token = callback.get('payment_token')

                    # Mettre à jour la commande avec le payment_token et le statut
                    order.payment_stripe_token = payment_token
                    order.status = 'payment_pending'  # Ou 'completed' si payé
                    order.save()

                    return Response({
                        'payment_url': payment_url,
                        'payment_token': payment_token,
                    })
                else:
                    return Response({"error": "Invalid response format"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                # return Response({"error": "Payment failed"}, status=status.HTTP_400_BAD_REQUEST)
                try:
                        response_data = response.json()  # Analyse la réponse JSON
                except ValueError:
                    response_data = response.text  # Si la réponse n'est pas du JSON, retourne le texte brut

                return Response({
                    "error": "Payment failed",
                    "status_code": response.status_code,
                    "response_data": response_data  # Affiche la réponse JSON de Stripe
                }, status=status.HTTP_400_BAD_REQUEST)
        except requests.RequestException as e:
            return Response({"error": f"Request failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(["POST"])
def stripe_webhook(request):
    payload = request.body
    sig_header = request.headers.get("Stripe-Signature")

    # Vérification des entêtes nécessaires
    if not sig_header or not payload:
        return JsonResponse({"error": "Missing required headers or payload"}, status=400)

    try:
        # Construction de l'événement Stripe
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        return JsonResponse({"error": f"Webhook validation failed: {str(e)}"}, status=400)

    # Extraction des données de l'événement
    event_type = event.get("type")
    session = event.get("data", {}).get("object", {})
    session_id = session.get("id")

    if not session_id:
        return JsonResponse({"error": "Session ID missing"}, status=400)

    # Récupération de la commande liée à la session Stripe
    order = get_object_or_404(Order, payment_stripe_token=session_id)

    # Récupérer tous les OrderItem associés à cette commande
    order_items = order.items.all()

    # Pour chaque OrderItem, récupérer les Tickets associés et mettre à jour is_payment_done
    for order_item in order_items:
        # Récupérer les Tickets associés à cet OrderItem
        tickets = []
        for subclass in Ticket.__subclasses__():
            tickets.extend(subclass.objects.filter(order_item=order_item))

        # Mettre à jour is_payment_done pour chaque Ticket
        for ticket in tickets:
            ticket.is_payment_done = True
            ticket.save()

    # Mettre à jour le statut de l'Order
    if event_type == "checkout.session.completed":
        order.payment_done = True
        order.status = 'paid'
    elif event_type == "checkout.session.async_payment_succeeded":
        order.payment_done = True
        order.status = 'paid'
    elif event_type == "checkout.session.async_payment_failed":
        order.payment_done = False
        order.status = 'failed'
    elif event_type == "checkout.session.expired":
        order.payment_done = False
        order.status = 'expired'
    else:
        # Événement non pris en charge
        return JsonResponse({"status": "event ignored"}, status=200)

    # Sauvegarder les modifications de l'Order
    order.save()

    return JsonResponse({"status": "success"}, status=200)





class SuccessPageAPIView(APIView):
    schema = AutoSchema()

    def get(self, request, user_id):
        if not user_id:
            return Response({"error": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(id=user_id)
            cart = MyCart.objects.filter(user=user)
            order = Order.objects.filter(user=user)

            if not cart.exists():
                return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

            # Simuler une requête à l'API BuyPassFromCartAPIView
            token = Token.objects.get(user=user)
            buy_pass_api_url = f"{os.getenv('ROOT_URL_API')}purchase-from-cart/"
            headers = {'Authorization': f'Token {token.key}'}

            response = requests.post(buy_pass_api_url, headers=headers)

            if response.status_code == 200:
                print("kkkkkkkkkkkkkkkkkkkkkkk")

                  # Uncomment if you want to clear the cart upon successful purchase
                try:

                    email_html = f'''Hi {user.first_name},
                                \nYour payment has been received for the order.\n\nThank you'''

                    send_mail(
                        "Paiement Successfully",
                        email_html,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=False
                    )
                    cart.delete()
                    return Response({'redirect_url': 'http://localhost:4200/success'}, status=status.HTTP_200_OK)

                except SMTPException as e:
                    return Response(
                        {
                            'msg': str(e),

                        },
                        status=status.HTTP_404_NOT_FOUND
                    )

            else:
                return Response(
                    {"error": response.json().get("error", "An error occurred")},
                    status=response.status_code
                )

        except CustomUser.DoesNotExist:
            return Response({"error": f"User with ID {user_id} not found"}, status=status.HTTP_404_NOT_FOUND)

        except Token.DoesNotExist:
            return Response({"error": "Token not found for the user"}, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CancelPageAPIView(APIView):
    schema = AutoSchema()

    def get(self, request):
        return render(request, 'cancel_page.html')


class WavePaymentAPIView(APIView):
    schema = AutoSchema()

    def post(self, request):
        logged_in_user = request.data.get('user_id')
        user = EndUserDetail.objects.get(user=logged_in_user)

        events_amount = request.data.get('events_amount')

        if not events_amount:
            return Response({"error": "Missing 'events_amount' in request data"}, status=status.HTTP_400_BAD_REQUEST)

        customer_name = user.first_name
        customer_surname = user.second_name
        customer_number = user.telephone_number
        customer_birthday = "1998-05-20"
        customer_location = user.address
        user_id = user.id
        url = reverse('payment-response', kwargs={'user_id': user_id})
        success_url = "http://localhost:4200/success"
        cancel_url = request.build_absolute_uri(reverse('payment-cancel'))

        order_id = uuid.uuid4().hex
        missing_fields = []

        # Check if any of the required fields are empty
        if not customer_name:
            missing_fields.append("first_name")
        if not customer_surname:
            missing_fields.append("second_name")
        if not customer_number:
            missing_fields.append("telephone_number")
        if not customer_location:
            missing_fields.append("address")

        # If any fields are missing, return a response with the missing field names
        if missing_fields:
            return Response({"error": "Required user fields are missing", "missing_fields": missing_fields}, status=status.HTTP_400_BAD_REQUEST)

        payload = {
            "customer_name": customer_name,
            "customer_surname": customer_surname,
            "customer_number": customer_number,
            "customer_birthday": customer_birthday,
            "customer_location": customer_location,
            "callbackCancelUrl": cancel_url,
            "callbackSuccessUrl": success_url,
            "amount": events_amount,
            "order_id": order_id
        }
        print("PLAYLOADDDDD "+str(payload))
        headers = {
            'X-API-Key': '81bdf51c909897d5cb7755ab880fe52e',
            'Content-Type': 'application/json'
        }

        url = 'https://www.xaamga-cashless.tv/paywall/api/wave/payment/'

        try:
            response = requests.post(url, json=[payload], headers=headers)

            if response.status_code == 200:
                response_data = response.json()
                wave_launch_url = response_data[0]['Response']['wave_launch_url']

                return Response({
                    'payment_url': wave_launch_url,
                    "payment_status": "processing"
                })
            else:
                return Response({"error": "Payment failed"}, status=status.HTTP_400_BAD_REQUEST)
        except requests.RequestException as e:
            return Response({"error": f"Request failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CinetpayGroupPaymentAPIView(APIView):
    schema = AutoSchema()

    def post(self, request):
        logged_in_user = request.data.get('user_id')
        user = EndUserDetail.objects.get(user=logged_in_user)

        events_amount = request.data.get('events_amount')

        if not events_amount:
            return Response({"error": "Missing 'events_amount' in request data"}, status=status.HTTP_400_BAD_REQUEST)

        customer_name = user.first_name
        customer_surname = user.second_name
        customer_number = user.telephone_number
        customer_birthday = "1998-05-20"
        customer_location = user.address
        user_id = user.id
        url = reverse('payment-response', kwargs={'user_id': user_id})
        success_url = request.build_absolute_uri(url)
        cancel_url = request.build_absolute_uri(reverse('payment-cancel'))

        order_id = uuid.uuid4().hex
        transaction_id = uuid.uuid4().hex
        missing_fields = []

        # Check if any of the required fields are empty
        if not customer_name:
            missing_fields.append("first_name")
        if not customer_surname:
            missing_fields.append("second_name")
        if not customer_number:
            missing_fields.append("telephone_number")
        if not customer_location:
            missing_fields.append("address")

        # If any fields are missing, return a response with the missing field names
        if missing_fields:
            return Response({"error": "Required user fields are missing", "missing_fields": missing_fields}, status=status.HTTP_400_BAD_REQUEST)

        payload = {
            "customer_name": customer_name,
            "customer_surname": customer_surname,
            "customer_number": customer_number,
            "customer_birthday": customer_birthday,
            "customer_location": customer_location,
            "event_currency": "XOF",
            "cancel_url": cancel_url,
            "success_url": success_url,
            "channels":"WALLET",
            "transaction_id":transaction_id,
            "events_amount": events_amount,
            "order_id": order_id
        }

        headers = {
            'X-API-Key': '81bdf51c909897d5cb7755ab880fe52e',
            'Content-Type': 'application/json'
        }

        url = 'https://www.xaamga-cashless.tv/paywall/api/cinetpay/paymentCinetpay/'

        try:
            response = requests.post(url, json=[payload], headers=headers)
            if response.status_code == 200:
                response_text = response.text
                response_data = json.loads(response_text.replace('\\"', '"'))

                if isinstance(response_data, list) and len(response_data) > 0:
                    callback = response_data[0].get('callback', {})
                    payment_url = callback.get('payment_url')
                    print(payment_url)
                    payment_token = callback.get('payment_token')

                    return render(request, 'initiate_stripe_payment.html', {
                        'payment_url': payment_url,
                        'payment_token': payment_token,
                    })
                else:
                    return Response({"error": "Invalid response format"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"error": "Payment failed"}, status=status.HTTP_400_BAD_REQUEST)
        except requests.RequestException as e:
            return Response({"error": f"Request failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# class OrangePaymentAPIView(APIView):
#     def post(self, request):
#         logged_in_user = request.data.get('user_id')
#         user = EndUserDetail.objects.get(user=logged_in_user)

#         events_amount = request.data.get('events_amount')
#         if not events_amount:
#             return Response({"error": "Missing 'events_amount' in request data"}, status=status.HTTP_400_BAD_REQUEST)

#         customer_name = user.first_name
#         customer_surname = user.second_name
#         customer_number = user.telephone_number
#         customer_birthday = "1998-05-20"
#         customer_location = user.address
#         user_id = user.id
#         url = reverse('payment-response', kwargs={'user_id': user_id})
#         success_url = request.build_absolute_uri(url)
#         cancel_url = request.build_absolute_uri(reverse('payment-cancel'))
#         order_id = uuid.uuid4().hex
#         missing_fields = []

#         # Check if any of the required fields are empty
#         if not customer_name:
#             missing_fields.append("first_name")
#         if not customer_surname:
#             missing_fields.append("second_name")
#         if not customer_number:
#             missing_fields.append("telephone_number")
#         if not customer_location:
#             missing_fields.append("address")

#         # If any fields are missing, return a response with the missing field names
#         if missing_fields:
#             return Response({"error": "Required user fields are missing", "missing_fields": missing_fields}, status=status.HTTP_400_BAD_REQUEST)

#         # Payload for the POST request
#         payload = {
#             "customer_name": customer_name,
#             "customer_surname": customer_surname,
#             "customer_number": customer_number,
#             "customer_birthday": customer_birthday,
#             "customer_location": customer_location,
#             "callbackCancelUrl": cancel_url,
#             "callbackSuccessUrl": success_url,
#             "amount": events_amount,
#             "order_id": order_id
#         }

#         headers = {
#             'X-API-Key': '81bdf51c909897d5cb7755ab880fe52e',
#             'Content-Type': 'application/json'
#         }

#         url = 'https://www.xaamga-cashless.tv/paywall/api/orangemoney/qr-code-generator/'

#         try:
#             response = requests.post(url, json=[payload], headers=headers)
#             if response.status_code == 200:
#                 response_data = response.json()
#                 print(response_data[0])
#                 deepLink = response_data[0]['Response']['deepLink']
#                 qrCode = response_data[0]['Response']['qrCode']
#                 return Response({
#                     'deepLink': deepLink,
#                     'qrCode': qrCode
#                 })
#             else:
#                 return Response({"error": "Payment failed"}, status=status.HTTP_400_BAD_REQUEST)
#         except requests.RequestException as e:
            # return Response({"error": f"Request failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrangePaymentAPIView(APIView):
    schema = AutoSchema()

    def post(self, request):
        user_id = request.data.get('user_id')
        events_amount = request.data.get('events_amount')

        if not user_id or not events_amount:
            missing_fields = []
            if not user_id:
                missing_fields.append("user_id")
            if not events_amount:
                missing_fields.append("events_amount")
            return Response({"error": "Missing required fields", "missing_fields": missing_fields}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = EndUserDetail.objects.get(user=user_id)
        except EndUserDetail.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        customer_data = {
            "customer_name": user.first_name,
            "customer_surname": user.second_name,
            "customer_number": user.telephone_number,
            "customer_birthday": "1998-05-20",
            "customer_location": user.address
        }

        missing_fields = [field for field, value in customer_data.items() if not value]
        if missing_fields:
            return Response({"error": "Required user fields are missing", "missing_fields": missing_fields}, status=status.HTTP_400_BAD_REQUEST)

        payment_data = {
            "callbackCancelUrl": settings.FRONTEND_URL+"/error",
            "callbackSuccessUrl": settings.FRONTEND_URL+"/success",
            "amount": events_amount,
            "order_id": uuid.uuid4().hex,
        }
        payload = {**customer_data, **payment_data}
        
        headers = {'X-API-Key': '81bdf51c909897d5cb7755ab880fe52e', 'Content-Type': 'application/json'}
        url = 'https://www.xaamga-cashless.tv/paywall/api/orangemoney/qr-code-generator/'

        try:
            response = requests.post(url, json=[payload], headers=headers)
            if response.status_code != 200:
                return Response({"error": "Payment failed"}, status=status.HTTP_400_BAD_REQUEST)

            response_data = response.json()[0]['Response']
            buy_pass_response = self.buy_pass_from_cart(user)
            if buy_pass_response.status_code != status.HTTP_200_OK:
                return Response({"error": "Buy pass from cart failed"}, status=buy_pass_response.status_code)

            return Response({
                'deepLink': response_data['deepLink'],
                'qrCode': response_data['qrCode'],
                "payment_status": "processing"
            })

        except requests.RequestException as e:
            return Response({"error": f"Request failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def buy_pass_from_cart(self, user):
        from home.api.EndUserAPIs import BuyPassFromCartAPIView

        request = self.request._request
        request.user = user.user

        try:
            token = Token.objects.get(user=user.user)
            request.META['HTTP_AUTHORIZATION'] = f'Token {str(token)}'
            response = BuyPassFromCartAPIView.as_view()(request)

            if response.status_code == status.HTTP_200_OK:
                return response

            error_messages = {
                status.HTTP_401_UNAUTHORIZED: "Authentication credentials were not provided.",
                status.HTTP_403_FORBIDDEN: "You do not have permission to perform this action.",
                status.HTTP_400_BAD_REQUEST: response.data
            }

            return Response({"error": error_messages.get(response.status_code, "Unexpected error occurred during the buy pass process.")}, status=response.status_code)

        except (NotAuthenticated, PermissionDenied, ValidationError) as e:
            return Response({"error": str(e)}, status=e.status_code)
        except Exception as e:
            return Response({"error": f"Exception: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
