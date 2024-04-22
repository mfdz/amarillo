from fastapi import HTTPException
import pytest
from amarillo.services.oauth2 import verify_permission
from amarillo.models.User import User

test_user = User(user_id="test", password="testpassword", permissions=["all:read", "mfdz:write", "ride2go:all", "metrics"])
admin_user = User(user_id="admin", password="testpassword", permissions=["admin"])

def test_operation():
    verify_permission("metrics", test_user)

    with pytest.raises(HTTPException):
        verify_permission("geojson", test_user)

def test_agency_permission():
    verify_permission("mvv:read", test_user)
    verify_permission("mfdz:read", test_user)
    verify_permission("mfdz:write", test_user)
    verify_permission("ride2go:write", test_user)

    with pytest.raises(HTTPException):
        verify_permission("mvv:write", test_user)
        verify_permission("mvv:all", test_user)


def test_admin():
    verify_permission("admin", admin_user)
    verify_permission("all:all", admin_user)
    verify_permission("mvv:all", admin_user)
    verify_permission("mfdz:read", admin_user)
    verify_permission("mfdz:write", admin_user)
    verify_permission("ride2go:write", admin_user)

    with pytest.raises(HTTPException):
        verify_permission("admin", test_user)
        verify_permission("all:all", test_user)