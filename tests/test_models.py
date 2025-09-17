import pytest
from pydantic import ValidationError

from src.models import WorkItem


class TestWorkItem:
    def test_work_item_valid_creation(self):
        """Test WorkItem can be created with valid data"""
        work_item = WorkItem(
            job_id="test-job-123",
            task="fill_login",
            payload={"username": "testuser", "password": "secret"},
        )

        assert work_item.job_id == "test-job-123"
        assert work_item.task == "fill_login"
        assert work_item.payload == {"username": "testuser", "password": "secret"}

    def test_work_item_missing_job_id(self):
        """Test WorkItem raises ValidationError when job_id is missing"""
        with pytest.raises(ValidationError) as exc_info:
            WorkItem(task="fill_login", payload={"username": "testuser"})

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("job_id",)
        assert errors[0]["type"] == "missing"

    def test_work_item_missing_task(self):
        """Test WorkItem raises ValidationError when task is missing"""
        with pytest.raises(ValidationError) as exc_info:
            WorkItem(job_id="test-job-123", payload={"username": "testuser"})

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("task",)
        assert errors[0]["type"] == "missing"

    def test_work_item_missing_payload(self):
        """Test WorkItem raises ValidationError when payload is missing"""
        with pytest.raises(ValidationError) as exc_info:
            WorkItem(job_id="test-job-123", task="fill_login")

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("payload",)
        assert errors[0]["type"] == "missing"

    def test_work_item_empty_payload(self):
        """Test WorkItem accepts empty payload dict"""
        work_item = WorkItem(job_id="test-job-123", task="screenshot", payload={})

        assert work_item.payload == {}

    def test_work_item_complex_payload(self):
        """Test WorkItem accepts complex nested payload"""
        complex_payload = {
            "user": {"name": "John Doe", "credentials": {"username": "john", "password": "secret"}},
            "settings": {"timeout": 30, "retry_count": 3},
            "files": ["doc1.pdf", "doc2.xlsx"],
        }

        work_item = WorkItem(
            job_id="complex-job-456", task="process_documents", payload=complex_payload
        )

        assert work_item.payload == complex_payload

    def test_work_item_json_serialization(self):
        """Test WorkItem can be serialized to JSON"""
        work_item = WorkItem(
            job_id="test-job-789", task="automation_task", payload={"key": "value", "number": 42}
        )

        json_data = work_item.model_dump()

        assert json_data == {
            "job_id": "test-job-789",
            "task": "automation_task",
            "payload": {"key": "value", "number": 42},
        }

    def test_work_item_from_dict(self):
        """Test WorkItem can be created from dictionary"""
        data = {
            "job_id": "dict-job-001",
            "task": "web_scraping",
            "payload": {"url": "https://example.com", "depth": 2},
        }

        work_item = WorkItem(**data)

        assert work_item.job_id == "dict-job-001"
        assert work_item.task == "web_scraping"
        assert work_item.payload == {"url": "https://example.com", "depth": 2}

    def test_work_item_string_representation(self):
        """Test WorkItem has proper string representation"""
        work_item = WorkItem(job_id="str-test-001", task="test_task", payload={"test": True})

        str_repr = str(work_item)
        assert "str-test-001" in str_repr
        assert "test_task" in str_repr
