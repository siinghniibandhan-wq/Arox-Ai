import unittest
from app.coding_gateway import is_allowed_model

class CodingGatewayTests(unittest.TestCase):
    def test_general_models_allowed(self):
        for model in ("arox-smart", "arox-flash", "arox-complex"):
            with self.subTest(model=model):
                self.assertTrue(is_allowed_model(model))

    def test_public_model_rejected(self):
        self.assertFalse(is_allowed_model("arox-public"))

    def test_unknown_and_empty_models_rejected(self):
        for model in ("unknown-model", "", None):
            with self.subTest(model=model):
                self.assertFalse(is_allowed_model(model))

if __name__ == "__main__":
    unittest.main()
