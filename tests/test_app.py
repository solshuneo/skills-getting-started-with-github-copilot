"""
FastAPI backend tests using AAA (Arrange-Act-Assert) pattern
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestGetActivities:
    """Test GET /activities endpoint"""
    
    def test_returns_dictionary_of_activities(self):
        """Verify that activities endpoint returns a dict"""
        # Arrange
        expected_type = dict
        
        # Act
        response = client.get("/activities")
        result = response.json()
        
        # Assert
        assert response.status_code == 200
        assert isinstance(result, expected_type)
    
    def test_activity_contains_required_fields(self):
        """Verify activities have all required fields"""
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        chess_activity = activities["Chess Club"]
        
        # Assert
        assert all(field in chess_activity for field in required_fields)
        assert isinstance(chess_activity["participants"], list)
    
    def test_activities_include_all_expected_clubs(self):
        """Verify all expected activities are present"""
        # Arrange
        expected_activities = {
            "Chess Club", "Programming Class", "Gym Class",
            "Basketball Team", "Swimming Club", "Art Studio",
            "Drama Club", "Science Club", "Math Olympiad"
        }
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        assert expected_activities.issubset(set(activities.keys()))


class TestSignupForActivity:
    """Test POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_participant_succeeds(self):
        """Verify a new participant can sign up"""
        # Arrange
        activity_name = "Programming Class"
        new_email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name.replace(' ', '%20')}/signup"
            f"?email={new_email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert new_email in response.json()["message"]
    
    def test_duplicate_signup_returns_error(self):
        """Verify duplicate signups are rejected"""
        # Arrange
        activity_name = "Art Studio"
        duplicate_email = "duplicate@mergington.edu"
        
        # Act - First signup
        client.post(
            f"/activities/{activity_name.replace(' ', '%20')}/signup"
            f"?email={duplicate_email}"
        )
        
        # Act - Duplicate signup attempt
        response = client.post(
            f"/activities/{activity_name.replace(' ', '%20')}/signup"
            f"?email={duplicate_email}"
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_for_nonexistent_activity_returns_404(self):
        """Verify signup to non-existent activity returns 404"""
        # Arrange
        fake_activity = "Nonexistent Club"
        email = "user@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{fake_activity.replace(' ', '%20')}/signup"
            f"?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_signup_adds_participant_to_list(self):
        """Verify signed up participant appears in activity participants"""
        # Arrange
        activity_name = "Drama Club"
        signup_email = "drama_student@mergington.edu"
        
        # Act - Get initial state
        response = client.get("/activities")
        initial_participants = response.json()[activity_name]["participants"].copy()
        
        # Act - Sign up
        client.post(
            f"/activities/{activity_name.replace(' ', '%20')}/signup"
            f"?email={signup_email}"
        )
        
        # Act - Get updated state
        response = client.get("/activities")
        updated_participants = response.json()[activity_name]["participants"]
        
        # Assert
        assert len(updated_participants) == len(initial_participants) + 1
        assert signup_email in updated_participants


class TestRemoveParticipant:
    """Test DELETE /activities/{activity_name}/participants endpoint"""
    
    def test_remove_existing_participant_succeeds(self):
        """Verify an existing participant can be removed"""
        # Arrange
        activity_name = "Science Club"
        email_to_remove = "science@mergington.edu"
        
        # Act - Add participant
        client.post(
            f"/activities/{activity_name.replace(' ', '%20')}/signup"
            f"?email={email_to_remove}"
        )
        
        # Act - Remove participant
        response = client.delete(
            f"/activities/{activity_name.replace(' ', '%20')}/participants"
            f"?email={email_to_remove}"
        )
        
        # Assert
        assert response.status_code == 200
        assert "Removed" in response.json()["message"]
    
    def test_remove_nonexistent_participant_returns_404(self):
        """Verify removing non-existent participant returns 404"""
        # Arrange
        activity_name = "Math Olympiad"
        nonexistent_email = "notreal@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name.replace(' ', '%20')}/participants"
            f"?email={nonexistent_email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_remove_from_nonexistent_activity_returns_404(self):
        """Verify removing from non-existent activity returns 404"""
        # Arrange
        fake_activity = "Fake Activity"
        email = "user@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{fake_activity.replace(' ', '%20')}/participants"
            f"?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
    
    def test_remove_reduces_participant_count(self):
        """Verify participant is removed from activity participants list"""
        # Arrange
        activity_name = "Swimming Club"
        email_to_remove = "swimmer@mergington.edu"
        
        # Act - Add participant
        client.post(
            f"/activities/{activity_name.replace(' ', '%20')}/signup"
            f"?email={email_to_remove}"
        )
        
        # Act - Get count before removal
        response = client.get("/activities")
        count_before_removal = len(response.json()[activity_name]["participants"])
        
        # Act - Remove participant
        client.delete(
            f"/activities/{activity_name.replace(' ', '%20')}/participants"
            f"?email={email_to_remove}"
        )
        
        # Act - Get count after removal
        response = client.get("/activities")
        count_after_removal = len(response.json()[activity_name]["participants"])
        
        # Assert
        assert count_after_removal == count_before_removal - 1
        assert email_to_remove not in response.json()[activity_name]["participants"]


class TestRootEndpoint:
    """Test GET / endpoint"""
    
    def test_root_redirects_to_static(self):
        """Verify root endpoint redirects to static HTML"""
        # Arrange
        expected_status = 307  # Temporary redirect
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == expected_status
        assert "/static/index.html" in response.headers["location"]
