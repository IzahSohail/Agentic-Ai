import unittest

from main import DEFAULT_CHOICES, app, store


class ChoiceApiTests(unittest.TestCase):
    def setUp(self) -> None:
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_choices_reset_to_default_on_refresh(self) -> None:
        store.choices = ["Maybe", "Later"]
        response = self.client.get("/api/choices")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"choices": DEFAULT_CHOICES})

    def test_posting_choices_keeps_yes_no_defaults(self) -> None:
        response = self.client.post("/api/choices", json={"choices": ["A", "B", "C"]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"choices": DEFAULT_CHOICES})


if __name__ == "__main__":
    unittest.main()
