from flask import url_for
from flask_testing import TestCase
from app import sa, create_app as create_application
from app.models import User, Role


class MainViewsFormsTestCase(TestCase):
    render_templates = False

    def create_app(self):
        app = create_application('testing')
        return app

    def setUp(self):
        sa.drop_all()
        sa.create_all()
        Role.initialize_roles()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        sa.session.remove()
        sa.drop_all()
        sa.create_all()

    def test_landing_page_render(self):
        response = self.client.get(url_for('main.landing'))
        self.assert_template_used('public/index.html')

    def test_custom_404_error(self):
        path = '/non_existent_endpoint'
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed('errors/404.html')
