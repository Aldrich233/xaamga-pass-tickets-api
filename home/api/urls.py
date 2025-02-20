from django.urls import path

from home.api.payment_gateway import *
from . import payment_gateway
from .socialLogin import *
from .SuperAdminAPIs import *
from .partnerAPIs import *
from .clientAPIs import *
from .eventAPIs import *
from .EndUserAPIs import *
from .nfc import *
from .TeamApis import *




urlpatterns = [
    # SUPERADMIN API URLS 
    path('generate-random-user/', RandomUserAPIView.as_view(), name='generate_random_user'),
    path('get-all-users/', GetAllUserList.as_view(), name='user-list'),
    path('update-delete-users/', UpdateAndDeleteUsers.as_view(), name='update-delete-user'),
    path('partner/register/', PartnerRegister.as_view(), name='partner_register'),
    path('admin/register/', AdminRegister.as_view(), name='admin_register'),
    path('client/register/', ClientRegister.as_view(), name='client_register'),
    path('event/create/', CreateEvent.as_view(), name='event_create'),
    path('partners-list/', PartnerListView.as_view(), name='partner-list'),
    path('event-list/', EventList.as_view(), name='events-list'),
    # path('events/<int:event_id>/services/', UniqueEventTeamList.as_view(), name='event-services'),
    path('clients-list/', ClientListView.as_view(), name='clients-list'),
    path('partner-details/<int:pk>/', PartnerDetailsView.as_view(), name='partner-details'),
    path('client-details/<int:pk>/', ClientDetailsView.as_view(), name='client-details'),
    path('event-team-register/', EventTeamCreateView.as_view(), name='event-team-register'),
    # path('events/<int:event_id>/teams/', EventTeamByTypeAPIView.as_view(), name='event-teams-by-type'),
    # path('event-update-teams/<int:pk>/', EventTeamRetrieveUpdateDestroyAPIView.as_view(), name='event-team-detail'),
    #ADD PASS PRICE URL
    # path('add-pass-prices/', PassPriceListCreateView.as_view(), name='pass-price-list-create'),
    # path('update-pass-prices/<int:pk>/', PassPriceRetrieveUpdateDestroyView.as_view(), name='pass-price-retrieve-update-destroy'),
    path('event/<int:event_id>/service-prices/', ServicePriceAPIView.as_view(), name='event-service-prices'),
    #LOGOUT
    path('logout/', LogoutView.as_view(), name='logout'),

    #ADD BRACLET PRICE 
    # path('add-bracelet-prices/', BraceletPriceListCreateView.as_view(), name='bracelet-price-list-create'),
    # path('update-bracelet-prices/<int:pk>/', BraceletPriceRetrieveUpdateDestroyView.as_view(), name='bracelet-price-retrieve-update-destroy'),

    #ADD SERVICES PRICE
    path('add-service-prices/', ServicePriceListCreateView.as_view(), name='service-price-list-create'),
    path('update-service-prices/<int:pk>/', ServicePriceRetrieveUpdateDestroyView.as_view(), name='service-price-retrieve-update-destroy'), 


    #ADMIN API URLS
    path('admin/login/', AdminLoginAPIView.as_view(), name='admin-login'),
    path('admin-update-details/<int:pk>/', AdminCustomUserDetailAPIView.as_view(), name='admin-update-details'),

#__________________________________________webAPI__________________________________________________________
    # path('create-event1/', CreateEvents1.as_view(), name='createevent'),
    # path('create-event2/<int:evnt_id>', CreateEvents2.as_view(), name='createevent2'),
    # path('create-event3/<int:evnt_id>', CreateEvents3.as_view(), name='createevent3'),
    # path('create-event4/<int:evnt_id>', CreateEvents4.as_view(), name='createevent4'),
    # path('active-deactive/<int:evnt_id>', ActiveDeactiveEvent.as_view(), name='ActiveAndDeactiveEvent'),

    #PARTNER API URLS
    path('partner/login/', PartnerLoginAPIView.as_view(), name='partner-login'),
    path('create-event-by-partner/', CreateEventByPartner.as_view(), name='create-event-by-partner'),
    path('client-register-by-partner/', ClientRegisterByPartner.as_view(), name='client-register-by-partner'),
    path('partner-update-details/<int:pk>/', PartnerCustomUserDetailAPIView.as_view(), name='partner-update-details'),
    path('update-description/', PartnerDescriptionUpdate.as_view(), name='update-description'),


    #CLIENT API URLS
    path('client/login/', ClientLoginAPIView.as_view(), name='client-login'),
    path('client-update-details/<int:pk>/', ClientCustomUserDetailAPIView.as_view(), name='client-update-details'),


    #EVENT API URLS
    path('event/login/', EventLoginAPIView.as_view(), name='event-login'),
    path('event-update-details/<int:pk>/', EventCustomUserDetailAPIView.as_view(), name='event-update-details'),
    path('EventDetailsprice/<int:event_id>/', EventPriceDetails.as_view(), name='EventDetails'),
    path('event/<int:event_id>/qrcode/', EventQRCodeAPIView.as_view(), name='event_qrcode'),


    #END_USER API URLS
    path('end-user/register/', EndUserRegisterAPIView.as_view(), name='end-user-register'),
    path('end-user/register-google/', EndUserRegisterGoogleAPIView.as_view(), name='end-user-register'),
    path('end-user/login/', EndUserLoginAPIView.as_view(), name='end-user-login'),
    path('end-user/login-google/', EndUserLoginAPIView.as_view(), name='end-user-login'),
    # path('verify-email/', EmailVerificationAPIView.as_view(), name='verify-email'),
    # path('verify-email/<str:token>/', EmailVerificationAPIView.as_view(), name='verify-email'),
    path('verify-email/', EmailVerificationAPIView.as_view(), name='verify-email'),
    
    path('forget-password/', ForgotPasswordView.as_view(), name='forget-password'),
    path('verify-otp/', verify_otp, name='verify_otp'),
    path('reset-password/', reset_password, name='reset_password'),
    path('event/<int:event_id>/passes/', EventPassPriceAPIView.as_view(), name='event-pass-price'),
    path('event/buy_pass/', BuyPassAPIView.as_view(), name='buy-pass'),
    # path('event/<int:event_id>/buy_pass/', BuyPassAPIView.as_view(), name='buy-pass'),
    path('user-purchase-ticket/', GetUserPurchaseTicket.as_view(), name='user-purchase-ticket'),
    path('add-to-cart/', AddToCart.as_view(), name='add-to-cart'),
    path('get-cart-items/', GetCartItems.as_view(), name='get-cart-items'),
    path('purchase-from-cart/', BuyPassFromCartAPIView.as_view(), name='purchase-from-cart'),
    path('remove-increase-product-cart/<int:pk>/', RemoveOrIncreaseProductFromCartView.as_view(), name='remove-increase-product-to-cart'),
    path('decrease-product-cart/<int:pk>/', DecreaseProductFromCartView.as_view(), name='remove-increase-product-to-cart'),
    path('type-of-events/', CategoryEventList.as_view(), name='event-list'),
    path('events/category/<int:category_id>/', EventsByCategoryAPIView.as_view(), name='events-by-category'),
    path('events/category/name/<str:category_name>/', EventsByCategoryNameAPIView.as_view(), name='events-by-category-name'),
    path('events/category/', EventsByCategoryNameAPIView.as_view(), name='events-by-category-name'),
    path('events/filter/', EventFilterList.as_view(), name='event-filter'),
    path('user-profile/', UserProfile.as_view(), name='user-profile'),
    path('favorite_events/', FavoriteEventList.as_view(), name='favorite_events'),
    path('remove_favorite_event/<int:event_id>/', RemoveFavoriteEvent.as_view(), name='remove_favorite_event'),
    path('send-gift/', SendGiftAPI.as_view(), name='send-gift'),


    #TEAM APIs 
    path('team/login/', TeamLoginAPIView.as_view(), name='team-login'),
    # path('drinks-team/login/', DrinksTeamLoginAPIView.as_view(), name='drinks-user-login'),
    # path('food-court-team/login/', FoodCourtTeamLoginAPIView.as_view(), name='food-court-login'),
    # path('activity-team/login/', ActivityTeamLoginAPIView.as_view(), name='activity-login'),
    # path('check-in-team/login/', CheckInTeamLoginAPIView.as_view(), name='check-in-login'),
    path('team-profile-data/', EventTeamProfileAPIView.as_view(), name='team-profile-data'),
    path('get-pass-event-guichet/', GetPassesOfEventGuichet.as_view(), name='get-pass-event-guichet'),
    path('get-bracelet-event-guichet/', GetBracletOfEventGuichet.as_view(), name='get-bracelet-event-guichet'),
    # path('team/login/', GuichetTeamLoginAPIView.as_view(), name='end-user-login'),

    #NFC API URLS

    path('read/<str:nfc_id>/', NFCReadView.as_view(), name='nfc-read'),
    # path('check-in/<str:nfc_id>/', CheckInNFCID.as_view(), name='check-in'),
    path('write/', NFCWriteView.as_view(), name='nfc-write'),

    #--------------------------------payment gateways--------------------------------#
    path('stripe-payment/initiate/', StripeGroupPaymentAPIView.as_view() , name='initiate-payment'),
    path('payment/response/<int:user_id>/', SuccessPageAPIView.as_view(), name='payment-response'),
    path('payment-cancel/', CancelPageAPIView.as_view(), name='payment-cancel'),

    path('webhooks/stripe/', payment_gateway.stripe_webhook, name='stripe-webhook'),

#--------------------------CINTEPAY GATEWAY----------------------------------------------#
    path('cinetpay-payment/initiate/', CinetpayGroupPaymentAPIView.as_view() , name='cinetpay-initiate-payment'),
#--------------------------WAVE GATEWAY----------------------------------------------#
    path('wave-payment/initiate/', WavePaymentAPIView.as_view() , name='wave-initiate-payment'),
#--------------------------ORANGE GATEWAY----------------------------------------------#
    path('orange-payment/initiate/', OrangePaymentAPIView.as_view() , name='orange-initiate-payment'),

    path('v3/convert/', ConvertCurrencyView.as_view(), name='convert_currency'),
    path('translate/', TranslateView.as_view(), name='translate'),
    
    # path('rest-auth/google/', GoogleSignup.as_view(), name='google_login'),
    path("~redirect/", view=UserRedirectView.as_view(), name="redirect"),

    path('google-login/', GoogleLogin.as_view(), name='google-login'),
    path('google-callback/', GoogleCallback.as_view(), name='google-callback'),
    path('google-profile/', GoogleProfile.as_view(), name='google-profile'),
    path('facebook/', FacebookSocialAuthView.as_view()),


    

]



