class TestEmptyAndMissingTitle:
    def test_create_with_empty_title(self, client):
        response = client.post("/tasks/", json={"title": ""})
        assert response.status_code == 422

    def test_create_with_missing_title(self, client):
        response = client.post("/tasks/", json={"description": "No title here"})
        assert response.status_code == 422

    def test_create_with_null_title(self, client):
        response = client.post("/tasks/", json={"title": None})
        assert response.status_code == 422


class TestTitleBoundaryValues:
    def test_create_with_single_char_title(self, client):
        response = client.post("/tasks/", json={"title": "A"})
        assert response.status_code == 201
        assert response.json()["title"] == "A"

    def test_create_with_max_length_title(self, client):
        title = "A" * 255
        response = client.post("/tasks/", json={"title": title})
        assert response.status_code == 201
        assert len(response.json()["title"]) == 255

    def test_create_with_too_long_title(self, client):
        title = "A" * 300
        response = client.post("/tasks/", json={"title": title})
        assert response.status_code == 422


class TestInvalidEnumValues:
    def test_create_with_invalid_status(self, client):
        response = client.post(
            "/tasks/", json={"title": "Task", "status": "invalid"}
        )
        assert response.status_code == 422

    def test_create_with_invalid_priority(self, client):
        response = client.post(
            "/tasks/", json={"title": "Task", "priority": "critical"}
        )
        assert response.status_code == 422

    def test_create_with_numeric_status(self, client):
        response = client.post(
            "/tasks/", json={"title": "Task", "status": "123"}
        )
        assert response.status_code == 422

    def test_create_with_empty_status(self, client):
        response = client.post(
            "/tasks/", json={"title": "Task", "status": ""}
        )
        assert response.status_code == 422


class TestNonExistentResources:
    def test_get_non_existent_task(self, client):
        response = client.get("/tasks/99999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"

    def test_update_non_existent_task(self, client):
        response = client.put("/tasks/99999", json={"title": "Ghost"})
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"

    def test_delete_non_existent_task(self, client):
        response = client.delete("/tasks/99999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"


class TestUpdateEdgeCases:
    def test_update_with_empty_body(self, client):
        create_resp = client.post("/tasks/", json={"title": "Stable"})
        task_id = create_resp.json()["id"]

        response = client.put(f"/tasks/{task_id}", json={})
        assert response.status_code == 200
        assert response.json()["title"] == "Stable"

    def test_update_preserves_unchanged_fields(self, client):
        create_resp = client.post(
            "/tasks/",
            json={
                "title": "Original",
                "description": "Keep me",
                "status": "pending",
                "priority": "high",
            },
        )
        task_id = create_resp.json()["id"]

        response = client.put(f"/tasks/{task_id}", json={"status": "completed"})
        data = response.json()
        assert data["title"] == "Original"
        assert data["description"] == "Keep me"
        assert data["priority"] == "high"
        assert data["status"] == "completed"


class TestSpecialCharacters:
    def test_title_with_special_characters(self, client):
        special_title = 'Test <>&"\'!@#$%^&*()'
        response = client.post("/tasks/", json={"title": special_title})
        assert response.status_code == 201
        assert response.json()["title"] == special_title

    def test_description_with_special_characters(self, client):
        special_desc = "Line1\nLine2\tTabbed & <tagged> \"quoted\""
        response = client.post(
            "/tasks/", json={"title": "Special", "description": special_desc}
        )
        assert response.status_code == 201
        assert response.json()["description"] == special_desc

    def test_title_with_unicode(self, client):
        unicode_title = "Tarea importante"
        response = client.post("/tasks/", json={"title": unicode_title})
        assert response.status_code == 201
        assert response.json()["title"] == unicode_title

    def test_title_with_emoji(self, client):
        emoji_title = "Fix bug in production"
        response = client.post("/tasks/", json={"title": emoji_title})
        assert response.status_code == 201
        assert response.json()["title"] == emoji_title


class TestMalformedRequests:
    def test_post_with_no_body(self, client):
        response = client.post("/tasks/")
        assert response.status_code == 422

    def test_post_with_extra_fields(self, client):
        response = client.post(
            "/tasks/",
            json={"title": "Task", "unknown_field": "value"},
        )
        assert response.status_code == 201

    def test_get_tasks_with_negative_skip(self, client):
        response = client.get("/tasks/?skip=-1")
        assert response.status_code == 422

    def test_get_tasks_with_zero_limit(self, client):
        response = client.get("/tasks/?limit=0")
        assert response.status_code == 422

    def test_get_tasks_with_excessive_limit(self, client):
        response = client.get("/tasks/?limit=999")
        assert response.status_code == 422


class TestResponseTimeValidation:
    def test_create_task_response_time(self, client):
        import time

        start = time.time()
        response = client.post("/tasks/", json={"title": "Speed Test"})
        duration = time.time() - start

        assert response.status_code == 201
        assert duration < 1.0

    def test_list_tasks_response_time(self, client):
        import time

        for i in range(20):
            client.post("/tasks/", json={"title": f"Task {i}"})

        start = time.time()
        response = client.get("/tasks/")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 1.0
