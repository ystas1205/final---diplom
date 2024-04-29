from django.urls import path, include, re_path
from django_rest_passwordreset.views import reset_password_request_token, \
    reset_password_confirm
from backend.views import ContactView, ShopView, RegisterAccount, \
    ConfirmAccount, LoginAccount, ProductInfoView, BasketView, PartnerUpdate, \
    AccountDetails, OrderView, CategoryView, PartnerState, Partnerexport, \
    Sentrytest

app_name = 'backend'

urlpatterns = [
    path('partner/update', PartnerUpdate.as_view(), name='partner-update'),
    path('partner/export', Partnerexport.as_view(), name='part-export'),
    path('user/register', RegisterAccount.as_view(), name='user-register'),
    path('user/register/confirm', ConfirmAccount.as_view(),
         name='user-register-confirm'),
    path('user/login', LoginAccount.as_view(), name='user-login'),
    path('user/password_reset', reset_password_request_token,
         name='password-reset'),
    path('user/password_reset/confirm', reset_password_confirm,
         name='password-reset-confirm'),
    path('user/details', AccountDetails.as_view(), name='user-details'),
    path('user/contact', ContactView.as_view(), name='user-contact'),
    path('shops', ShopView.as_view(), name='shops'),
    path('products', ProductInfoView.as_view(), name='shops'),
    path('partner/state', PartnerState.as_view(), name='partner-state'),

    path('basket', BasketView.as_view(), name='basket'),
    path('order', OrderView.as_view(), name='order'),
    path('categories', CategoryView.as_view(), name='categories'),
    path('order', OrderView.as_view(), name='order'),
    path('sentrytest', Sentrytest.as_view(), name='sentrytest')

]
