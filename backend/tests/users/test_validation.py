import pytest
from django.core.exceptions import ValidationError as DjangoValidationError
from marshmallow.exceptions import ValidationError

from common.validation import SchemaError, load_data_from_schema
from users import validation
from users.models import User


def test_NumberValidator():
    validation.NumberValidator(minimum=1).validate("1")


def test_UppercaseValidator():
    validation.UppercaseValidator(minimum=1).validate("A")


def test_LowercaseValidator():
    validation.LowercaseValidator(minimum=1).validate("a")


def test_SymbolValidator():
    validation.SymbolValidator(minimum=1).validate("$")


def test_NumberValidator_zero():
    validation.NumberValidator(minimum=0).validate("")


def test_UppercaseValidator_zero():
    validation.UppercaseValidator(minimum=0).validate("")


def test_LowercaseValidator_zero():
    validation.LowercaseValidator(minimum=0).validate("")


def test_SymbolValidator_zero():
    validation.SymbolValidator(minimum=0).validate("")


def test_NumberValidator_not_enough():
    with pytest.raises(DjangoValidationError):
        validation.NumberValidator(minimum=2).validate("1")


def test_UppercaseValidator_not_enough():
    with pytest.raises(DjangoValidationError):
        validation.UppercaseValidator(minimum=2).validate("A")


def test_LowercaseValidator_not_enough():
    with pytest.raises(DjangoValidationError):
        validation.LowercaseValidator(minimum=2).validate("a")


def test_SymbolValidator_not_enough():
    with pytest.raises(DjangoValidationError):
        validation.SymbolValidator(minimum=2).validate("$")


@pytest.mark.parametrize("symbol", validation.SymbolValidator.symbols)
def test_SymbolValidator_all_valid_chars(symbol):
    validation.SymbolValidator(minimum=1).validate(symbol)


def test_NumberValidator_help_text():
    assert validation.NumberValidator(minimum=1).get_help_text() == (
        "This password must contain at least 1 digit(s), 0-9."
    )
    assert validation.NumberValidator(minimum=2).get_help_text() == (
        "This password must contain at least 2 digit(s), 0-9."
    )


def test_UppercaseValidator_help_text():
    assert validation.UppercaseValidator(minimum=1).get_help_text() == (
        "This password must contain at least 1 uppercase letter, A-Z."
    )
    assert validation.UppercaseValidator(minimum=2).get_help_text() == (
        "This password must contain at least 2 uppercase letter, A-Z."
    )


def test_LowercaseValidator_help_text():
    assert validation.LowercaseValidator(minimum=1).get_help_text() == (
        "This password must contain at least 1 lowercase letter, a-z."
    )
    assert validation.LowercaseValidator(minimum=2).get_help_text() == (
        "This password must contain at least 2 lowercase letter, a-z."
    )


def test_SymbolValidator_help_text():
    assert validation.SymbolValidator(minimum=1).get_help_text() == (
        r"This password must contain at least 1 symbol: ()[]{}|\`~!@#$%^&*_-+=;:'\",<>./?"
    )
    assert validation.SymbolValidator(minimum=2).get_help_text() == (
        r"This password must contain at least 2 symbol: ()[]{}|\`~!@#$%^&*_-+=;:'\",<>./?"
    )


def make_valid_password():
    # make a password that passed alsl validaiton criteria
    return User.objects.make_random_password() + "aA$1"


def test_reset_check_schema_all_ok():
    data = {
        "reset_key": "reset_key",
    }
    result = validation.ResetPasswordCheckSchema().load(data)

    assert result == data


def test_reset_password_schema_all_ok():
    password = make_valid_password()
    data = {
        "reset_key": "reset_key",
        "password1": password,
        "password2": password,
    }
    result = validation.ResetPasswordCompleteSchema().load(data)

    assert result == data


def test_reset_password_load_data_from_schema_invalid():
    data = {
        "reset_key": "reset_key",
        "password1": "pass",
        "password2": "pass",
    }
    with pytest.raises(SchemaError) as e:
        load_data_from_schema(
            validation.ResetPasswordCompleteSchema(), data
        )
    assert e.value.errors["password1"] == [
        "This password is too short. It must contain at least 8 characters.",
        "This password is too common.",
        "This password must contain at least 1 digit(s), 0-9.",
        "This password must contain at least 1 uppercase letter, A-Z.",
        "This password must contain at least 1 symbol: ()[]{}|\\`~!@#$%^&*_-+=;:'\\\",<>./?",
    ]


def test_reset_password_complete_load_data_from_schema_passwords_dont_match():
    password1 = make_valid_password()
    password2 = make_valid_password()
    data = {
        "reset_key": "reset_key",
        "password1": password1,
        "password2": password2,
    }
    with pytest.raises(SchemaError) as e:
        load_data_from_schema(
            validation.ResetPasswordCompleteSchema(), data
        )
    assert e.value.errors["password2"] == [
        "Passwords must match."
    ]


@pytest.mark.django_db
def test_ActivateCheckSchema_valid_key(mocker):

    user = User.objects.create(username="user")
    check_activation_key = mocker.patch("users.validation.User.check_activation_key", return_value=(user, None))

    schema = validation.ActivateCheckSchema()
    result = schema.load({"activate_key": "activate_key"})

    assert result == {"activate_key": "activate_key", "user": user}

    assert check_activation_key.mock_calls == [mocker.call("activate_key")]


@pytest.mark.django_db
def test_ActivateCheckSchema_bad_key(mocker):

    user = User.objects.create(username="user")
    check_activation_key = mocker.patch("users.validation.User.check_activation_key",
                                        side_effect=[(None, None), (None, None)])

    schema = validation.ActivateCheckSchema()
    with pytest.raises(ValidationError) as ve:
        schema.load({"activate_key": "activate_key"})

    assert ve.value.messages["activate_key"] == [
        "Sorry that activation key is not valid."
    ]
    assert check_activation_key.mock_calls == [mocker.call("activate_key"), mocker.call("activate_key", max_age=None)]


@pytest.mark.django_db
def test_ActivateCheckSchema_expired_key(mocker):

    user = User.objects.create(username="user", email="user@example.com")
    check_activation_key = mocker.patch("users.validation.User.check_activation_key",
                                        side_effect=[(None, None), (user, None)])
    send_account_activation_email = mocker.patch("users.validation.User.send_account_activation_email")

    schema = validation.ActivateCheckSchema()
    with pytest.raises(ValidationError) as ve:
        schema.load({"activate_key": "activate_key"})

    assert ve.value.messages["activate_key"] == [
        "That token has expired. A new email has been sent to your address. Please click on the new link in the email."
    ]
    assert check_activation_key.mock_calls == [mocker.call("activate_key"), mocker.call("activate_key", max_age=None)]
    assert send_account_activation_email.mock_calls == [mocker.call()]


@pytest.mark.django_db
def test_ActivateSchema_valid_key(mocker):

    user = User.objects.create(username="username")
    check_activation_key = mocker.patch("users.validation.User.check_activation_key", return_value=(user, None))

    password = make_valid_password()

    data = {
        "activate_key": "activate_key",
        "username": "username",
        "password1": password,
        "password2": password,
        "first_name": "first_name",
        "last_name": "last_name",
    }
    schema = validation.ActivateSchema()
    result = schema.load(data)

    assert result == {
        "activate_key": "activate_key",
        "username": "username",
        "password1": password,
        "password2": password,
        "first_name": "first_name",
        "last_name": "last_name",
        "user": user
    }

    assert check_activation_key.mock_calls == [mocker.call("activate_key")]


@pytest.mark.django_db
def test_ActivateSchema_valid_key_changing_username(mocker):

    user = User.objects.create(username="username")
    check_activation_key = mocker.patch("users.validation.User.check_activation_key", return_value=(user, None))

    password = make_valid_password()

    data = {
        "activate_key": "activate_key",
        "username": "new_username",
        "password1": password,
        "password2": password,
        "first_name": "first_name",
        "last_name": "last_name",
    }
    schema = validation.ActivateSchema()
    result = schema.load(data)

    assert result == {
        "activate_key": "activate_key",
        "username": "new_username",
        "password1": password,
        "password2": password,
        "first_name": "first_name",
        "last_name": "last_name",
        "user": user
    }

    assert check_activation_key.mock_calls == [mocker.call("activate_key")]


@pytest.mark.django_db
def test_ActivateSchema_requesting_non_unique_username(mocker):

    user = User.objects.create(username="user")
    User.objects.create(username="otheruser", email="otheruser@tempurl.com")

    mocker.patch("users.validation.User.check_activation_key", return_value=(user, None))

    password = make_valid_password()

    data = {
        "activate_key": "activate_key",
        "username": "otheruser",
        "password1": password,
        "password2": password,
        "first_name": "first_name",
        "last_name": "last_name",
    }
    schema = validation.ActivateSchema()
    with pytest.raises(ValidationError) as ve:
        schema.load(data)

    assert ve.value.messages["username"] == [
        "Sorry that username is not available."
    ]


@pytest.mark.django_db
def test_ActivateSchema_valid_key_password_not_valid(mocker):

    user = User.objects.create(username="user")
    mocker.patch("users.validation.User.check_activation_key", return_value=(user, None))

    data = {
        "activate_key": "activate_key",
        "username": "username",
        "password1": "pass",
        "password2": "pass",
        "first_name": "first_name",
        "last_name": "last_name",
    }

    schema = validation.ActivateSchema()
    with pytest.raises(ValidationError) as ve:
        schema.load(data)

    assert ve.value.messages["password1"] == [
        "This password is too short. It must contain at least 8 characters.",
        "This password is too common.",
        "This password must contain at least 1 digit(s), 0-9.",
        "This password must contain at least 1 uppercase letter, A-Z.",
        "This password must contain at least 1 symbol: ()[]{}|\\`~!@#$%^&*_-+=;:'\\\",<>./?",
    ]


@pytest.mark.django_db
def test_ActivateSchema_valid_key_username_with_space(mocker):

    user = User.objects.create(username="user")
    mocker.patch("users.validation.User.check_activation_key", return_value=(user, None))

    data = {
        "activate_key": "activate_key",
        "username": "username with space",
        "password1": "password",
        "password2": "password",
        "first_name": "first_name",
        "last_name": "last_name",
    }

    schema = validation.ActivateSchema()
    with pytest.raises(ValidationError) as ve:
        schema.load(data)

    assert ve.value.messages["username"] == [
        "Enter a valid username. This value may contain only letters, numbers, and @/./+/-/_ characters."
    ]


@pytest.mark.django_db
def test_ActivateSchema_valid_key_username_too_short(mocker):

    user = User.objects.create(username="user")
    mocker.patch("users.validation.User.check_activation_key", return_value=(user, None))

    data = {
        "activate_key": "activate_key",
        "username": "u",
        "password1": "password",
        "password2": "password",
        "first_name": "first_name",
        "last_name": "last_name",
    }

    schema = validation.ActivateSchema()
    with pytest.raises(ValidationError) as ve:
        schema.load(data)

    assert ve.value.messages["username"] == [
        "Sorry that username is too short, must be 3 characters or more."
    ]


@pytest.mark.django_db
def test_ActivateSchema_passwords_must_match(mocker):

    user = User.objects.create(username="user")
    mocker.patch("users.validation.User.check_activation_key", return_value=(user, None))

    password = make_valid_password()

    data = {
        "activate_key": "activate_key",
        "username": "user",
        "password1": password,
        "password2": User.objects.make_random_password(),  # different password2
        "first_name": "first_name",
        "last_name": "last_name",
    }

    schema = validation.ActivateSchema()
    with pytest.raises(ValidationError) as ve:
        schema.load(data)
    print(ve.value.messages)
    assert ve.value.messages["password1"] == [
        "Passwords must match."
    ]
