import re
import unittest
from pathlib import Path
from unittest.mock import PropertyMock, patch

import app as web
from werkzeug.security import check_password_hash, generate_password_hash


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.result = None
        self.rowcount = 1

    def execute(self, query, params=None):
        self.connection.executed.append((query, params))
        self.result = self.connection.user_row if query.startswith(
            "SELECT * FROM users WHERE email="
        ) else None

    def fetchone(self):
        return self.result

    def fetchall(self):
        return []

    def close(self):
        pass


class FakeConnection:
    def __init__(self, user_row=None):
        self.user_row = user_row
        self.executed = []
        self.commits = 0

    def cursor(self):
        return FakeCursor(self)

    def commit(self):
        self.commits += 1


class HospitalAppTests(unittest.TestCase):
    def setUp(self):
        web.app.config.update(TESTING=True)
        self.client = web.app.test_client()
        self.csrf_token = "test-csrf-token"

    def set_session(self, **values):
        with self.client.session_transaction() as flask_session:
            flask_session.update(values)

    def post_with_csrf(self, path, data=None):
        payload = dict(data or {})
        payload["csrf_token"] = self.csrf_token
        return self.client.post(path, data=payload)

    def mock_connection(self, connection):
        return patch.object(
            type(web.mysql),
            "connection",
            new_callable=PropertyMock,
            return_value=connection,
        )

    def test_post_without_csrf_token_is_rejected(self):
        response = self.client.post("/signup", data={"name": "Sam"})
        self.assertEqual(response.status_code, 400)

    def test_signup_cannot_assign_privileged_role_and_hashes_password(self):
        connection = FakeConnection()
        self.set_session(csrf_token=self.csrf_token)
        with self.mock_connection(connection):
            response = self.post_with_csrf(
                "/signup",
                {
                    "name": "Sam Patient",
                    "email": "sam@example.com",
                    "password": "strong-password",
                    "role": "admin",
                },
            )

        self.assertEqual(response.status_code, 302)
        insert = next(
            (query, params)
            for query, params in connection.executed
            if query.startswith("INSERT INTO users")
        )
        self.assertEqual(insert[1][3], "patient")
        self.assertTrue(check_password_hash(insert[1][2], "strong-password"))

    def test_login_uses_hashed_password_and_redirects_by_role(self):
        hashed = generate_password_hash("secret")
        connection = FakeConnection((7, "Pat", "pat@example.com", hashed, "patient"))
        self.set_session(csrf_token=self.csrf_token)
        with self.mock_connection(connection):
            response = self.post_with_csrf(
                "/login",
                {"email": "pat@example.com", "password": "secret"},
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/patient")
        self.assertEqual(connection.executed[0][0], "SELECT * FROM users WHERE email=%s")

    def test_legacy_plaintext_password_is_upgraded_after_login(self):
        connection = FakeConnection(
            (8, "Pat", "pat@example.com", "old-password", "patient")
        )
        self.set_session(csrf_token=self.csrf_token)
        with self.mock_connection(connection):
            response = self.post_with_csrf(
                "/login",
                {"email": "pat@example.com", "password": "old-password"},
            )

        self.assertEqual(response.status_code, 302)
        update_query, update = connection.executed[1]
        self.assertEqual(update_query, "UPDATE users SET password=%s WHERE id=%s")
        self.assertTrue(check_password_hash(update[0], "old-password"))

    def test_doctor_request_update_is_scoped_to_logged_in_doctor(self):
        connection = FakeConnection()
        self.set_session(
            csrf_token=self.csrf_token,
            user="doctor@example.com",
            role="doctor",
        )
        with self.mock_connection(connection):
            response = self.post_with_csrf("/accept/12")

        self.assertEqual(response.status_code, 302)
        query, params = connection.executed[0]
        self.assertIn("doctor_email=%s", query)
        self.assertEqual(params, (12, "doctor@example.com"))

    def test_patient_bill_update_is_scoped_to_logged_in_patient(self):
        connection = FakeConnection()
        self.set_session(
            csrf_token=self.csrf_token,
            user="pat@example.com",
            role="patient",
        )
        with self.mock_connection(connection):
            response = self.post_with_csrf("/pay_bill/22")

        self.assertEqual(response.status_code, 302)
        query, params = connection.executed[0]
        self.assertIn("patient_email=%s", query)
        self.assertEqual(params, (22, "pat@example.com"))

    def test_state_changing_routes_do_not_accept_get(self):
        self.set_session(user="doctor@example.com", role="doctor")
        paths = (
            "/accept/1",
            "/reject/1",
            "/delete_request/1",
            "/dispense/1",
            "/generate_bill/1",
            "/pay_bill/1",
            "/logout",
        )
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 405)

    def test_all_templates_parse(self):
        for template_name in web.app.jinja_env.list_templates():
            with self.subTest(template=template_name):
                web.app.jinja_env.get_template(template_name)

    def test_every_post_form_has_a_csrf_field(self):
        template_dir = Path(web.app.root_path) / web.app.template_folder
        for template_path in template_dir.glob("*.html"):
            source = template_path.read_text(encoding="utf-8")
            forms = re.findall(r"<form\b.*?</form>", source, re.IGNORECASE | re.DOTALL)
            for form in forms:
                if re.search(r'method=["\']POST["\']', form, re.IGNORECASE):
                    with self.subTest(template=template_path.name, form=form[:80]):
                        self.assertIn('name="csrf_token"', form)

    def test_signup_page_renders_csrf_token(self):
        response = self.client.get("/signup")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'name="csrf_token"', response.data)


if __name__ == "__main__":
    unittest.main()
