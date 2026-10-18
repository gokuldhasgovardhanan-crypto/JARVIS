import io
import json
from api.index import handler, detect_language, handle_intent


class MockServerlessRequest:
    def __init__(self, method: str, path: str, body: dict = None):
        self.command = method
        self.path = path
        self.rfile = io.BytesIO(json.dumps(body).encode("utf-8") if body else b"")
        self.wfile = io.BytesIO()
        self.headers = {"Content-Length": str(len(self.rfile.getvalue()))}
        self.status = None
        self.response_headers = {}

    def send_response(self, code):
        self.status = code

    def send_header(self, key, val):
        self.response_headers[key] = val

    def end_headers(self):
        pass


def test_language_detection():
    assert detect_language("what time is it") == "en"
    assert detect_language("நேரம் என்ன") == "ta"
    assert detect_language("samay batao") == "hi"
    assert detect_language("wie spät ist es") == "de"
    assert detect_language("notepad open pannu") == "ta"


def test_intent_handler():
    time_res = handle_intent("what time is it", "en")
    assert time_res["intent"] == "get_time"
    assert "current server time" in time_res["reply"]

    date_res = handle_intent("what is today's date", "en")
    assert date_res["intent"] == "get_date"
    assert "Today is" in date_res["reply"]


def test_serverless_handler_get():
    req = MockServerlessRequest("GET", "/api")
    h = handler.__new__(handler)
    h.headers = req.headers
    h.rfile = req.rfile
    h.wfile = req.wfile
    h.send_response = req.send_response
    h.send_header = req.send_header
    h.end_headers = req.end_headers

    h.do_GET()
    assert req.status == 200
    res = json.loads(req.wfile.getvalue().decode("utf-8"))
    assert res["status"] == "online"
    assert "supported_languages" in res


def test_serverless_handler_post_time():
    req = MockServerlessRequest("POST", "/api", body={"text": "what time is it", "preferred_language": "auto"})
    h = handler.__new__(handler)
    h.headers = req.headers
    h.rfile = req.rfile
    h.wfile = req.wfile
    h.send_response = req.send_response
    h.send_header = req.send_header
    h.end_headers = req.end_headers

    h.do_POST()
    assert req.status == 200
    res = json.loads(req.wfile.getvalue().decode("utf-8"))
    assert "current server time" in res["text"]
    assert res["detected_language"] == "en"
