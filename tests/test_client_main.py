from flask import url_for
from tests.test_client_utils import BaseClientTestCase


class MainViewsFormsTestCase(BaseClientTestCase):

    def test_landing_page_render(self):
        response = self.client.get(url_for('main.landing'))
        self.assertTemplateUsed('public/index.html')
        self.assert200(response)

    def test_custom_404_error(self):
        path = '/non_existent_endpoint'
        response = self.client.get(path)
        self.assertStatus(response, 404)
        self.assertTemplateUsed('errors/404.html')
