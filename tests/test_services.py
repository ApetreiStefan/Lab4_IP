"""
Teste unitare pentru ai_service/services/gemini_utils.py
și pentru serviciile care îl folosesc.

Strategia: mockăm genai.Client și os.getenv — nu facem niciun apel real la API.
"""

import json
import pytest
from unittest.mock import patch, MagicMock


# ==========================================
# TESTE PENTRU gemini_utils.py
# ==========================================

class TestGetApiKey:
    # _load_dotenv() este mockată în toate testele pentru că altfel
    # reîncarcă .env-ul și suprascrie os.environ după ce patch.dict l-a curățat.

    def test_returns_gemini_key_when_set(self):
        with patch("ai_service.services.gemini_utils._load_dotenv"), \
                patch.dict("os.environ", {"GEMINI_API_KEY": "test-key-123"}, clear=True):
            from ai_service.services.gemini_utils import get_api_key
            assert get_api_key() == "test-key-123"

    def test_returns_google_key_as_fallback(self):
        with patch("ai_service.services.gemini_utils._load_dotenv"), \
                patch.dict("os.environ", {"GOOGLE_API_KEY": "google-key-456"}, clear=True):
            from ai_service.services.gemini_utils import get_api_key
            assert get_api_key() == "google-key-456"

    def test_gemini_key_has_priority_over_google_key(self):
        with patch("ai_service.services.gemini_utils._load_dotenv"), \
                patch.dict("os.environ", {
                    "GEMINI_API_KEY": "gemini-key",
                    "GOOGLE_API_KEY": "google-key"
                }, clear=True):
            from ai_service.services.gemini_utils import get_api_key
            assert get_api_key() == "gemini-key"

    def test_returns_none_when_no_key(self):
        with patch("ai_service.services.gemini_utils._load_dotenv"), \
                patch.dict("os.environ", {}, clear=True):
            from ai_service.services.gemini_utils import get_api_key
            assert get_api_key() is None


class TestMissingKeyError:
    def test_returns_valid_json_string(self):
        from ai_service.services.gemini_utils import missing_key_error
        result = missing_key_error()
        parsed = json.loads(result)
        assert "error" in parsed
        assert "API key" in parsed["error"] or "GEMINI_API_KEY" in parsed["error"]


class TestCallGemini:
    def _make_mock_response(self, text: str):
        mock_response = MagicMock()
        mock_response.text = text
        return mock_response

    def _make_mock_client(self, response_text: str):
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = self._make_mock_response(response_text)
        return mock_client

    def test_no_api_key_returns_error(self):
        with patch("ai_service.services.gemini_utils.get_api_key", return_value=None):
            from ai_service.services.gemini_utils import call_gemini
            result = json.loads(call_gemini("some prompt"))
            assert "error" in result

    def test_success_extracts_json_array(self):
        fake_response = 'Some text before [{"q": "Q1", "a": "A1"}] some text after'
        with patch("ai_service.services.gemini_utils.get_api_key", return_value="key"), \
                patch("ai_service.services.gemini_utils.genai.Client") as mock_client_cls:
            mock_client_cls.return_value = self._make_mock_client(fake_response)
            from ai_service.services.gemini_utils import call_gemini
            result = call_gemini("prompt")
            parsed = json.loads(result)
            assert isinstance(parsed, list)
            assert parsed[0]["q"] == "Q1"

    def test_success_extracts_json_object(self):
        fake_response = 'Prefix {"key": "value"} suffix'
        with patch("ai_service.services.gemini_utils.get_api_key", return_value="key"), \
                patch("ai_service.services.gemini_utils.genai.Client") as mock_client_cls:
            mock_client_cls.return_value = self._make_mock_client(fake_response)
            from ai_service.services.gemini_utils import call_gemini
            result = call_gemini("prompt")
            parsed = json.loads(result)
            assert parsed["key"] == "value"

    def test_no_json_in_response_returns_error(self):
        fake_response = "This is just plain text with no JSON at all."
        with patch("ai_service.services.gemini_utils.get_api_key", return_value="key"), \
                patch("ai_service.services.gemini_utils.genai.Client") as mock_client_cls:
            mock_client_cls.return_value = self._make_mock_client(fake_response)
            from ai_service.services.gemini_utils import call_gemini
            result = json.loads(call_gemini("prompt"))
            assert "error" in result
            assert "Failed to extract" in result["error"]

    def test_invalid_json_in_response_returns_error(self):
        # "[not valid json]" → regex găsește "[not valid json]" (are [ și ])
        # → json.loads("[not valid json]") → JSONDecodeError → except json.JSONDecodeError
        fake_response = "[not valid json]"
        with patch("ai_service.services.gemini_utils.get_api_key", return_value="key"), \
                patch("ai_service.services.gemini_utils.genai.Client") as mock_client_cls:
            mock_client_cls.return_value = self._make_mock_client(fake_response)
            from ai_service.services.gemini_utils import call_gemini
            result = json.loads(call_gemini("prompt"))
            assert "error" in result
            assert "invalid JSON" in result["error"]

    def test_api_exception_returns_error(self):
        with patch("ai_service.services.gemini_utils.get_api_key", return_value="key"), \
                patch("ai_service.services.gemini_utils.genai.Client") as mock_client_cls:
            mock_client_cls.return_value.models.generate_content.side_effect = Exception("Network timeout")
            from ai_service.services.gemini_utils import call_gemini
            result = json.loads(call_gemini("prompt"))
            assert "error" in result
            assert "Network timeout" in result["error"]


# ==========================================
# TESTE PENTRU gen_finaltest.py
# ==========================================

class TestGenerateFinalMcqTest:
    def test_calls_call_gemini_with_prompt(self):
        expected_output = json.dumps([{"id": 1, "question": "Q1"}])
        with patch("ai_service.services.gen_finaltest.call_gemini", return_value=expected_output) as mock_call, \
                patch("ai_service.services.gen_finaltest.prompt_finaltest", return_value="mocked prompt"):
            from ai_service.services.gen_finaltest import generate_final_mcq_test
            result = generate_final_mcq_test("Math", "Lesson text", "easy")
            assert result == expected_output
            mock_call.assert_called_once_with("mocked prompt")

    def test_propagates_error_from_call_gemini(self):
        error_output = json.dumps({"error": "API or execution error: timeout"})
        with patch("ai_service.services.gen_finaltest.call_gemini", return_value=error_output), \
                patch("ai_service.services.gen_finaltest.prompt_finaltest", return_value="prompt"):
            from ai_service.services.gen_finaltest import generate_final_mcq_test
            result = generate_final_mcq_test("Math", "Lesson text", "hard")
            parsed = json.loads(result)
            assert "error" in parsed


# ==========================================
# TESTE PENTRU reformat_professor.py
# ==========================================

class TestRefineAcademicText:
    def test_calls_call_gemini_with_prompt(self):
        expected_output = json.dumps({"rewritten": "Text academic."})
        with patch("ai_service.services.reformat_professor.call_gemini", return_value=expected_output) as mock_call, \
                patch("ai_service.services.reformat_professor.prompt_reformat_professor", return_value="mocked prompt"):
            from ai_service.services.reformat_professor import refine_academic_text
            result = refine_academic_text("Physics", "messy text")
            assert result == expected_output
            mock_call.assert_called_once_with("mocked prompt")

    def test_propagates_error_from_call_gemini(self):
        error_output = json.dumps({"error": "No API key"})
        with patch("ai_service.services.reformat_professor.call_gemini", return_value=error_output), \
                patch("ai_service.services.reformat_professor.prompt_reformat_professor", return_value="prompt"):
            from ai_service.services.reformat_professor import refine_academic_text
            result = json.loads(refine_academic_text("Physics", "text"))
            assert "error" in result


# ==========================================
# TESTE PENTRU gen_popquiz_explain.py
# ==========================================

class TestGenerateAnswerExplanations:
    VALID_QUIZ = [
        {"question": "Q1?", "options": ["A", "B", "C"], "num_correct": 1},
        {"question": "Q2?", "options": ["X", "Y", "Z"], "num_correct": 2},
    ]
    VALID_ANSWERS = [["A"], ["X", "Y"]]

    def test_no_api_key_returns_error(self):
        with patch("ai_service.services.gen_popquiz_explain.get_api_key", return_value=None):
            from ai_service.services.gen_popquiz_explain import generate_answer_explanations
            result = json.loads(generate_answer_explanations("lesson", self.VALID_QUIZ, self.VALID_ANSWERS))
            assert "error" in result

    def test_success_with_list_input(self):
        expected = json.dumps([{"explanation": "ok"}])
        with patch("ai_service.services.gen_popquiz_explain.get_api_key", return_value="key"), \
                patch("ai_service.services.gen_popquiz_explain.call_gemini", return_value=expected):
            from ai_service.services.gen_popquiz_explain import generate_answer_explanations
            result = generate_answer_explanations("lesson", self.VALID_QUIZ, self.VALID_ANSWERS)
            assert result == expected

    def test_success_with_string_input(self):
        expected = json.dumps([{"explanation": "ok"}])
        quiz_str = json.dumps(self.VALID_QUIZ)
        with patch("ai_service.services.gen_popquiz_explain.get_api_key", return_value="key"), \
                patch("ai_service.services.gen_popquiz_explain.call_gemini", return_value=expected):
            from ai_service.services.gen_popquiz_explain import generate_answer_explanations
            result = generate_answer_explanations("lesson", quiz_str, self.VALID_ANSWERS)
            assert result == expected

    def test_invalid_json_string_input_returns_error(self):
        with patch("ai_service.services.gen_popquiz_explain.get_api_key", return_value="key"):
            from ai_service.services.gen_popquiz_explain import generate_answer_explanations
            result = json.loads(generate_answer_explanations("lesson", "not json {{", self.VALID_ANSWERS))
            assert "error" in result
            assert "Invalid quiz_json" in result["error"]

    def test_non_list_json_returns_error(self):
        with patch("ai_service.services.gen_popquiz_explain.get_api_key", return_value="key"):
            from ai_service.services.gen_popquiz_explain import generate_answer_explanations
            result = json.loads(generate_answer_explanations("lesson", '{"not": "a list"}', self.VALID_ANSWERS))
            assert "error" in result
            assert "JSON array" in result["error"]

    def test_mismatch_answers_count_returns_error(self):
        with patch("ai_service.services.gen_popquiz_explain.get_api_key", return_value="key"):
            from ai_service.services.gen_popquiz_explain import generate_answer_explanations
            result = json.loads(generate_answer_explanations("lesson", self.VALID_QUIZ, [["A"]]))
            assert "error" in result
            assert "Mismatch" in result["error"]


# ==========================================
# TESTE PENTRU gen_finaltest_explain.py
# ==========================================

class TestGradeAndExplainMcqTest:
    VALID_TEST = [
        {"question": "Q1?", "options": ["A", "B", "C"], "num_correct": 1},
        {"question": "Q2?", "options": ["X", "Y", "Z"], "num_correct": 2},
    ]
    VALID_ANSWERS = [["A"], ["X", "Y"]]

    def test_no_api_key_returns_error(self):
        with patch("ai_service.services.gen_finaltest_explain.get_api_key", return_value=None):
            from ai_service.services.gen_finaltest_explain import grade_and_explain_mcq_test
            result = json.loads(grade_and_explain_mcq_test("lesson", self.VALID_TEST, self.VALID_ANSWERS))
            assert "error" in result

    def test_success_with_list_input(self):
        expected = json.dumps([{"explanation": "ok", "is_fully_correct": True}])
        with patch("ai_service.services.gen_finaltest_explain.get_api_key", return_value="key"), \
                patch("ai_service.services.gen_finaltest_explain.call_gemini", return_value=expected):
            from ai_service.services.gen_finaltest_explain import grade_and_explain_mcq_test
            result = grade_and_explain_mcq_test("lesson", self.VALID_TEST, self.VALID_ANSWERS)
            assert result == expected

    def test_success_with_string_input(self):
        expected = json.dumps([{"explanation": "ok"}])
        test_str = json.dumps(self.VALID_TEST)
        with patch("ai_service.services.gen_finaltest_explain.get_api_key", return_value="key"), \
                patch("ai_service.services.gen_finaltest_explain.call_gemini", return_value=expected):
            from ai_service.services.gen_finaltest_explain import grade_and_explain_mcq_test
            result = grade_and_explain_mcq_test("lesson", test_str, self.VALID_ANSWERS)
            assert result == expected

    def test_invalid_json_string_returns_error(self):
        with patch("ai_service.services.gen_finaltest_explain.get_api_key", return_value="key"):
            from ai_service.services.gen_finaltest_explain import grade_and_explain_mcq_test
            result = json.loads(grade_and_explain_mcq_test("lesson", "bad json {{", self.VALID_ANSWERS))
            assert "error" in result
            assert "Invalid test_json" in result["error"]

    def test_non_list_json_returns_error(self):
        with patch("ai_service.services.gen_finaltest_explain.get_api_key", return_value="key"):
            from ai_service.services.gen_finaltest_explain import grade_and_explain_mcq_test
            result = json.loads(grade_and_explain_mcq_test("lesson", '{"not": "a list"}', self.VALID_ANSWERS))
            assert "error" in result
            assert "JSON array" in result["error"]

    def test_mismatch_answers_count_returns_error(self):
        with patch("ai_service.services.gen_finaltest_explain.get_api_key", return_value="key"):
            from ai_service.services.gen_finaltest_explain import grade_and_explain_mcq_test
            result = json.loads(grade_and_explain_mcq_test("lesson", self.VALID_TEST, [["A"]]))
            assert "error" in result
            assert "Mismatch" in result["error"]


# ==========================================
# TEST PENTRU _load_dotenv — ramura except
# ==========================================

class TestLoadDotenv:
    def test_load_dotenv_handles_import_error_gracefully(self):
        """Dacă dotenv nu e instalat, funcția nu aruncă excepție."""
        import importlib
        with patch("importlib.import_module", side_effect=ImportError("No module")):
            # Nu trebuie să arunce nicio excepție
            from ai_service.services.gemini_utils import _load_dotenv
            _load_dotenv()  # trebuie să treacă fără eroare


# ==========================================
# TESTE PENTRU gen_popquiz.py
# ==========================================

class TestGeneratePopQuiz:
    def test_calls_call_gemini_with_prompt(self):
        expected_output = '[{"question": "Q1", "options": ["A", "B"], "num_correct": 1}]'
        with patch("ai_service.services.gen_popquiz.call_gemini", return_value=expected_output) as mock_call, \
                patch("ai_service.services.gen_popquiz.prompt_popquiz", return_value="mocked prompt"):
            from ai_service.services.gen_popquiz import generate_pop_quiz
            result = generate_pop_quiz("Biology", "Lesson text", "medium")
            assert result == expected_output
            mock_call.assert_called_once_with("mocked prompt")

    def test_propagates_error_from_call_gemini(self):
        error_output = '{"error": "API or execution error: timeout"}'
        with patch("ai_service.services.gen_popquiz.call_gemini", return_value=error_output), \
                patch("ai_service.services.gen_popquiz.prompt_popquiz", return_value="prompt"):
            from ai_service.services.gen_popquiz import generate_pop_quiz
            result = json.loads(generate_pop_quiz("Biology", "Lesson text", "easy"))
            assert "error" in result
