import graphene
from graphene.utils import with_context

from django import forms
from django.contrib.auth import (
    authenticate,
    login as auth_login,
    logout as auth_logout
)
from django.contrib.auth.forms import (
    AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm,
    UserCreationForm as DjangoUserCreationForm
)
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import ugettext_lazy as _

from backend.fields import Error
from backend.mutations import Mutation
from .models_graphql import User
from .models import User as UserModel
from .decorators import login_required


def form_erros(form, errors=[]):
    for error_location, error_messages in form.errors.as_data().items():
        for error_instance in error_messages:
            for error_message in error_instance.messages:
                errors.append(Error(
                    code=error_instance.code,
                    location=error_location,
                    message=error_message,
                ))
    return errors


class UserCreationForm(DjangoUserCreationForm):
    class Meta:
        model = UserModel
        fields = ("username", "email", "first_name")

    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = True

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if UserModel.objects.filter(username=username).exists():
            raise forms.ValidationError(
                _("Este usuario já esta usado por outra pessoa. "
                  "Por favor, tente outro."),
                code='username_being_used',
            )
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if UserModel.objects.filter(email=email).exists():
            raise forms.ValidationError(
                _("Este e-mail já esta usado por outra pessoa. "
                  "Por favor, tente outro."),
                code='email_being_used',
            )
        return email


class Register(Mutation):
    class Input:
        first_name = graphene.String()
        username = graphene.String().NonNull
        email = graphene.String().NonNull
        password1 = graphene.String().NonNull
        password2 = graphene.String().NonNull

    user = graphene.Field(User)

    @classmethod
    @with_context
    def mutate_and_get_payload(cls, input, request, info):
        errors = []
        user = None

        form = UserCreationForm(data=input)
        if form.is_valid():
            user = form.save(commit=False)
            user.save(request=request)
        else:
            errors = form_erros(form, errors)
        return Register(user=user, errors=errors)


class RegisterAndAuthenticate(Register):
    @classmethod
    @with_context
    def mutate_and_get_payload(cls, input, request, info):
        register = super(
            RegisterAndAuthenticate,
            cls).mutate_and_get_payload(input, request, info)
        if register.user:
            # workarout to authenticate the user
            # it just needs the auth backend associated
            # to the user
            user_auth = authenticate(username=register.user.username,
                                     password=input.get('password1'))
            auth_login(request, user_auth)
        return RegisterAndAuthenticate(user=register.user,
                                       errors=register.errors)


class Authenticate(Mutation):
    class Input:
        username = graphene.String().NonNull
        password = graphene.String().NonNull

    @classmethod
    @with_context
    def mutate_and_get_payload(cls, input, request, info):
        errors = []
        user = None

        if request.user.is_authenticated():
            auth_logout(request)

        form = AuthenticationForm(data=input)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
        else:
            errors = form_erros(form, errors)
        return Authenticate(errors=errors)


class Deauthenticate(Mutation):
    class Input:
        pass

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, input, request, info):
        auth_logout(request)
        return Deauthenticate()


class PasswordChange(Mutation):
    class Input:
        new_password1 = graphene.String().NonNull
        new_password2 = graphene.String().NonNull
        old_password = graphene.String().NonNull

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, input, request, info):
        errors = []
        form = PasswordChangeForm(user=request.user, data=input)
        if form.is_valid():
            user = form.save(commit=False)
            user.save(request=request)

            # workarout to re authenticate the user
            # it just needs the auth backend associated
            # to the user
            user_auth = authenticate(username=user.username,
                                     password=input['new_password1'])
            auth_login(request, user_auth)
        else:
            errors = form_erros(form, errors)
        return PasswordChange(errors=errors)


class PasswordResetEmail(Mutation):
    class Input:
        email = graphene.String().NonNull

    @classmethod
    @with_context
    def mutate_and_get_payload(cls, input, request, info):
        errors = []
        form = PasswordResetForm(data=input)
        if form.is_valid():
            opts = {
                'use_https': request.is_secure(),
                'token_generator': default_token_generator,
                'from_email': None,
                'email_template_name': 'registration/password_reset_email.html',
                'subject_template_name': 'registration/password_reset_subject.txt',
                'request': request,
                'html_email_template_name': None,
                'extra_email_context': None,
            }
            form.save(**opts)
        else:
            errors = form_erros(form, errors)
        return PasswordChange(errors=errors)


class PasswordResetComplete(Mutation):
    class Input:
        uidb64 = graphene.String().NonNull
        token = graphene.String().NonNull
        new_password1 = graphene.String().NonNull
        new_password2 = graphene.String().NonNull

    @classmethod
    @with_context
    def mutate_and_get_payload(cls, input, request, info):
        errors = []
        UserModel = User._meta.model

        try:
            # urlsafe_base64_decode() decodes to bytestring on Python 3
            uid = force_text(urlsafe_base64_decode(input.get('uidb64')))
            user = UserModel.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
            user = None

        if user and default_token_generator.check_token(user, input.get('token')):
            form = SetPasswordForm(user=user, data=input)
            if form.is_valid():
                user = form.save(commit=False)
                user.save(request=request)

                # workarout to re authenticate the user
                # it just needs the auth backend associated
                # to the user
                user_auth = authenticate(username=user.username,
                                         password=input['new_password1'])
                auth_login(request, user_auth)
            else:
                errors = form_erros(form, errors)
        else:
            errors.append(Error(
                code='password_reset_incorrect_token',
                message=_('Password reset failed')
            ))

        return PasswordResetComplete(errors=errors)


class UserEditForm(forms.ModelForm):
    class Meta:
        model = UserModel
        fields = ("username", "email", "first_name")

    def __init__(self, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = True

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if UserModel.objects.filter(username=username).exclude(
                document_id=self.instance.document_id).exists():
            raise forms.ValidationError(
                _("Este usuario já esta usado por outra pessoa. "
                  "Por favor, tente outro."),
                code='username_being_used',
            )
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if UserModel.objects.filter(email=email).exclude(
                document_id=self.instance.document_id).exists():
            raise forms.ValidationError(
                _("Este e-mail já esta usado por outra pessoa. "
                  "Por favor, tente outro."),
                code='email_being_used',
            )
        return email


class ProfileEdit(Mutation):
    class Input:
        first_name = graphene.String()
        username = graphene.String().NonNull
        email = graphene.String().NonNull

    user = graphene.Field(User)

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, input, request, info):
        errors = []
        user = request.user

        form = UserEditForm(data=input, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            user.save(request=request)
        else:
            errors = form_erros(form, errors)
        return ProfileEdit(user=user, errors=errors)
