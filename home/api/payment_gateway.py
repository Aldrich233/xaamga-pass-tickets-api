from smtplib import SMTPException
from django.conf import settings
import json
import os
import uuid
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
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

STRIPE_WEBHOOK_SECRET = settings.STRIPE_WEBHOOK_SECRET

# class StripeGroupPaymentAPIView(APIView):
#
#     def post(self, request):
#         logged_in_user = request.data.get('user_id')
#         user = get_object_or_404(EndUserDetail, user=logged_in_user)
#         events_amount = request.data.get('events_amount')
#         events_amount = request.data.get('events_amount')
#         if not events_amount:
#             return Response({"error": "Missing 'events_amount' in request data"}, status=status.HTTP_400_BAD_REQUEST)
#
#         customer_name = user.first_name
#         customer_surname = user.second_name
#         customer_number = user.telephone_number
#         customer_birthday = "1998-05-20"
#         customer_location = user.address
#         user_id = user.id
#         url = reverse('payment-response', kwargs={'user_id': user_id})
#         success_url = request.build_absolute_uri(url)
#         print(success_url)
#         cancel_url = request.build_absolute_uri(reverse('payment-cancel'))
#
#         order_id = uuid.uuid4().hex
#         missing_fields = []
#
#         # Check if any of the required fields are empty
#         if not customer_name:
#             missing_fields.append("first_name")
#         if not customer_surname:
#             missing_fields.append("second_name")
#         if not customer_number:
#             missing_fields.append("telephone_number")
#         if not customer_location:
#             missing_fields.append("address")
#
#         # If any fields are missing, return a response with the missing field names
#         if missing_fields:
#             return Response({"error": "Required user fields are missing", "missing_fields": missing_fields}, status=status.HTTP_400_BAD_REQUEST)
#
#         # Check if any of the required fields are empty
#
#
#         payload = {
#             "customer_name": customer_name,
#             "customer_surname": customer_surname,
#             "customer_number": customer_number,
#             "customer_birthday": customer_birthday,
#             "customer_location": customer_location,
#             "cancel_url": cancel_url,
#             "success_url": success_url,
#             "events_amount": events_amount,
#             "order_id": order_id
#         }
#         print(payload)
#         headers = {
#             'X-API-Key': '81bdf51c909897d5cb7755ab880fe52e',
#             'Content-Type': 'application/json'
#         }
#
#         url = 'https://www.xaamga-cashless.tv/paywall/api/stripe/groupPayment/'
#
#         try:
#             response = requests.post(url, json=[payload], headers=headers)
#             print(response.status_code)
#             print(response.text)
#             if response.status_code == 200:
#                 response_text = response.text
#                 print(response_text)
#                 response_data = json.loads(response_text.replace('\\"', '"'))
#
#                 if isinstance(response_data, list) and len(response_data) > 0:
#                     callback = response_data[0].get('callback', {})
#                     payment_url = callback.get('payment_url')
#                     print(payment_url)
#                     payment_token = callback.get('payment_token')
#
#                     # payment_eTicket_instance =
#
#                     return Response({
#                         'payment_url': payment_url,
#                         'payment_token': payment_token,
#                     })
#                 else:
#                     return Response({"error": "Invalid response format"}, status=status.HTTP_400_BAD_REQUEST)
#             else:
#                 return Response({"error": "Payment failed"}, status=status.HTTP_400_BAD_REQUEST)
#         except requests.RequestException as e:
#             return Response({"error": f"Request failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StripeGroupPaymentAPIView(APIView):

    def post(self, request):
        # Récupérer l'utilisateur et la commande
        user_id = request.data.get('user_id')
        order_id = request.data.get('order_id')

        if not user_id or not order_id:
            return Response({"error": "Missing 'user_id' or 'order_id' in request data"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Récupérer l'utilisateur
        user = get_object_or_404(EndUserDetail, user=user_id)

        # Récupérer la commande
        order = get_object_or_404(Order, order_id=order_id, user=user)

        # Vérifier si la commande existe et récupérer le montant total
        events_amount = order.total_amount
        if not events_amount:
            return Response({"error": "Order has no total amount"}, status=status.HTTP_400_BAD_REQUEST)

        # Récupérer les informations de l'utilisateur pour le paiement
        customer_name = user.first_name
        customer_surname = user.second_name
        customer_number = user.telephone_number
        customer_birthday = "1998-05-20"  # Exemple de valeur
        customer_location = user.address

        # URL de redirection après succès ou échec du paiement
        success_url = request.build_absolute_uri(reverse('payment-response', kwargs={'user_id': user_id}))
        cancel_url = request.build_absolute_uri(reverse('payment-cancel'))

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
            "order_id": order.order_id  # Utilisation de l'order_id de la commande
        }

        print(payload)
        headers = {
            'X-API-Key': '81bdf51c909897d5cb7755ab880fe52e',
            'Content-Type': 'application/json'
        }

        url = 'https://www.xaamga-cashless.tv/paywall/api/stripe/groupPayment/'

        try:
            # Faire la requête Stripe
            response = requests.post(url, json=[payload], headers=headers)
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
                return Response({"error": "Payment failed"}, status=status.HTTP_400_BAD_REQUEST)
        except requests.RequestException as e:
            return Response({"error": f"Request failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(["POST"])
def stripe_webhook(request):
    payload = request.body
    sig_header = request.headers.get("Stripe-Signature")

    # Vérification de la signature et construction de l'événement
    if not sig_header or not payload:
        return JsonResponse({"error": "Missing required headers or payload"}, status=400)

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        return JsonResponse({"error": "Webhook validation failed"}, status=400)

    # Extraction des données de l'événement
    event_type = event.get("type")
    session = event.get("data", {}).get("object", {})
    session_id = session.get("id")

    if not session_id:
        return JsonResponse({"error": "Session ID missing"}, status=400)

    # Récupération de la transaction liée à l'événement
    try:
        transaction = Ticket.objects.get(payment_token=session_id)
    except Ticket.DoesNotExist:
        return JsonResponse({"error": "Transaction not found"}, status=404)

    # Récupération de la commande liée à la transaction
    try:
        order = Order.objects.get(payment_token=session_id)
    except Order.DoesNotExist:
        return JsonResponse({"error": "Order not found"}, status=404)

    # Gestion des événements Stripe et mise à jour des statuts
    try:
        if event_type == "checkout.session.completed":
            # Marquer le paiement comme effectué dans la commande et le ticket
            order.payment_done = True
            order.status = 'paid'
            order.is_payment_done = True  # Mise à jour de is_payment_done dans Order
            transaction.is_payment_done = True  # Mise à jour de is_payment_done dans Ticket
        elif event_type == "checkout.session.async_payment_succeeded":
            # Paiement réussi mais de manière asynchrone
            order.payment_done = True
            order.status = 'paid'
            order.is_payment_done = True
            transaction.is_payment_done = True
        elif event_type == "checkout.session.async_payment_failed":
            # Paiement échoué
            order.payment_done = False
            order.status = 'failed'
            order.is_payment_done = False
            transaction.is_payment_done = False
        elif event_type == "checkout.session.expired":
            # Session expirée
            order.payment_done = False
            order.status = 'expired'
            order.is_payment_done = False
            transaction.is_payment_done = False
        else:
            # Événement non pris en charge
            return JsonResponse({"status": "event ignored"}, status=200)

        # Sauvegarde des modifications dans les modèles
        order.save()
        transaction.save()
        return JsonResponse({"status": "success"}, status=200)

    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)



# def stripe_webhook(request):
#     payload = request.body
#     sig_header = request.headers.get("Stripe-Signature")
#
#     # logger.info(f"Payload reçu : {payload}")
#     # logger.info(f"Signature Stripe : {sig_header}")
#
#     # Vérification de la signature et construction de l'événement
#     if not sig_header or not payload:
#         # logger.error("Signature ou payload manquant.")
#         return JsonResponse({"error": "Missing required headers or payload"}, status=400)
#
#     try:
#         event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
#         # logger.info(f"Événement Stripe validé : {event['type']}")
#     except Exception as e:
#         # logger.error(f"Erreur lors de la validation du webhook : {str(e)}")
#         return JsonResponse({"error": "Webhook validation failed"}, status=400)
#
#     # Extraction des données de l'événement
#     event_type = event.get("type")
#     session = event.get("data", {}).get("object", {})
#     session_id = session.get("id")
#
#     if not session_id:
#         # logger.error("Session ID manquant ou non récupérable pour cet événement.")
#         return JsonResponse({"error": "Session ID missing"}, status=400)
#
#     # Récupération de la transaction
#     transaction = None
#     for _ in range(5):  # Réessaye 5 fois avec un délai de 2 secondes
#         try:
#             transaction = Ticket.objects.get(payment_token=session_id)
#             # logger.info(f"Transaction trouvée : {transaction.payment_token}")
#             break
#         except Ticket.DoesNotExist:
#             # logger.warning(f"Tentative {_+1}: Transaction introuvable pour session_id : {session_id}")
#             time.sleep(2)
#
#     if not transaction:
#         # logger.error(f"Transaction introuvable après plusieurs tentatives pour session_id : {session_id}")
#         return JsonResponse({"error": "Transaction not found"}, status=404)
#
#     # Récupération de la commande
#     try:
#         order = Order.objects.get(payment_token=session_id)
#         # logger.info(f"Commande trouvée : {order.order_id}")
#     except Order.DoesNotExist:
#         # logger.error(f"Commande introuvable pour session_id : {session_id}")
#         return JsonResponse({"error": "Order not found"}, status=404)
#
#     # Gestion des événements configurés
#     try:
#         if event_type == "checkout.session.completed":
#             transaction.order_payment_status = "paid"
#             order.payment_status = "paid"
#             # logger.info("Paiement marqué comme réussi (completed).")
#         elif event_type == "checkout.session.async_payment_succeeded":
#             transaction.order_payment_status = "paid"
#             order.payment_status = "paid"
#             # logger.info("Paiement marqué comme réussi (async_payment_succeeded).")
#         elif event_type == "checkout.session.async_payment_failed":
#             transaction.order_payment_status = "failed"
#             order.payment_status = "failed"
#             # logger.info("Paiement marqué comme échoué (async_payment_failed).")
#         elif event_type == "checkout.session.expired":
#             transaction.order_payment_status = "expired"
#             order.payment_status = "expired"
#             # logger.info("Session expirée (expired).")
#         else:
#             # logger.warning(f"Événement non pris en charge : {event_type}")
#             return JsonResponse({"status": "event ignored"}, status=200)
#
#         # Sauvegarde des modifications
#         transaction.save()
#         order.save()
#         # logger.info(f"Transaction et commande mises à jour avec succès pour la session {session_id}")
#         return JsonResponse({"status": "success"}, status=200)
#
#     except Exception as e:
#         # logger.error(f"Erreur inattendue : {str(e)}")
#         return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)



# class SuccessPageAPIView(APIView):
#     def get(self, request, user_id):
#         user_id = user_id

#         if not user_id:
#             return Response({"error": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             user = EndUserDetail.objects.get(id=user_id)
#             print(user.user.id)
#             cart = MyCart.objects.filter(user=user.user.id)
#             custom_user = CustomUser.objects.get(id = user.user.id)

#             pass_purchases = []

#             for cart_item in cart:
#                 event_id = cart_item.event_id
#                 pass_type = cart_item.pass_type
#                 quantity = cart_item.quantity
#                 price = cart_item.price

#                 try:
#                     event = Event.objects.get(id=event_id)
#                 except Event.DoesNotExist:
#                     raise ValidationError({"error": f"Event with ID {event_id} not found"}, code=404)

#                 try:
#                     updated_price = price
#                     total_price = updated_price * quantity
#                 except EventPassCategory.DoesNotExist:
#                     raise ValidationError({"error": f"Pass type '{pass_type}' not found for this event"}, code=404)

#                 try:
#                     event_pass = EventPassCategory.objects.get(event=event)
#                 except EventPassCategory.DoesNotExist:
#                     raise ValidationError({"error": "Event passes not found for this event"}, code=404)

#                 available_quantity = getattr(event_pass, f"{pass_type.lower()}_pass")
#                 if available_quantity < quantity:
#                     raise ValidationError({"error": f"Insufficient '{pass_type}' passes available"}, code=400)

#                 pass_purchase = ETicket.objects.create(
#                     event=event,
#                     user=custom_user,
#                     pass_type=pass_type,
#                     price=total_price,
#                     quantity=quantity,
#                     is_payment_done=True
#                 )

#                 # Decrease the available quantity of the specific pass type
#                 setattr(event_pass, f"{pass_type.lower()}_pass", available_quantity - quantity)
#                 event_pass.save()

#                 pass_purchases.append(pass_purchase)
#             cart.delete()
#             return redirect('http://localhost:4200')

#         except EndUserDetail.DoesNotExist:
#             raise ValidationError({"error": f"User with ID {user_id} not found"}, code=404)

#         except MyCart.DoesNotExist:
#             raise ValidationError({"error": f"Cart for user with ID {user_id} not found"}, code=404)

#         except Exception as e:
#             return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SuccessPageAPIView(APIView):
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
    def get(self, request):
        return render(request, 'cancel_page.html')


class WavePaymentAPIView(APIView):
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
