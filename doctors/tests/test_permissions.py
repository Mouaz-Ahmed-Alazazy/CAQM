
"""
Tests for permission denials and authorization failures.
Tests that users cannot access views they don't have permission for.
"""
import pytest
from django.urls import reverse
from django.contrib.messages import get_messages


@pytest.mark.django_db
class TestDoctorOnlyViewPermissions:
    """Test doctor-only views reject patients"""
    
    def test_patient_cannot_access_doctor_dashboard(self, authenticated_patient_client):
        """Test patient accessing doctor dashboard gets redirected"""
        url = reverse('doctors:doctor_dashboard')
        response = authenticated_patient_client.get(url)
        
        # Should redirect to login
        assert response.status_code == 302
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        assert any('Only doctors' in str(m) for m in messages)


@pytest.mark.django_db
class TestUnauthenticatedAccess:
    """Test unauthenticated users are redirected to login"""
    
    def test_unauthenticated_cannot_access_dashboard(self, client):
        """Test unauthenticated user accessing doctor dashboard"""
        url = reverse('doctors:doctor_dashboard')
        response = client.get(url)
        
        # Should redirect to login
        assert response.status_code == 302
        assert 'login' in response.url
