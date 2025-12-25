
"""
Tests for permission denials and authorization failures.
Tests that users cannot access views they don't have permission for.
"""
import pytest
from django.urls import reverse
from django.contrib.messages import get_messages


@pytest.mark.django_db
class TestPatientOnlyViewPermissions:
    """Test patient-only views reject doctors"""
    
    def test_doctor_cannot_book_appointment(self, authenticated_doctor_client):
        """Test doctor accessing book appointment page"""
        url = reverse('patients:book_appointment')
        response = authenticated_doctor_client.get(url)
        
        # Should redirect or show error
        assert response.status_code in [302, 403]
    
    def test_doctor_cannot_access_my_appointments(self, authenticated_doctor_client):
        """Test doctor accessing patient's my appointments page"""
        url = reverse('patients:my_appointments')
        response = authenticated_doctor_client.get(url)
        
        # Should redirect or show error
        assert response.status_code in [302, 403]


@pytest.mark.django_db
class TestUnauthenticatedAccess:
    """Test unauthenticated users are redirected to login"""
    
    def test_unauthenticated_cannot_book_appointment(self, client):
        """Test unauthenticated user booking appointment"""
        url = reverse('patients:book_appointment')
        response = client.get(url)
        
        assert response.status_code == 302
        assert 'login' in response.url
    
    def test_unauthenticated_cannot_access_my_appointments(self, client):
        """Test unauthenticated user accessing my appointments"""
        url = reverse('patients:my_appointments')
        response = client.get(url)
        
        assert response.status_code == 302
        assert 'login' in response.url
