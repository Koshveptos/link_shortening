
from locust import HttpUser, task, between
import random
import string


def generate_test_url() -> str:

    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"https://example.com/test/{suffix}"


class LinkShorteningUser(HttpUser):

    
    wait_time = between(0.5, 2.0)
    host = "http://localhost:8000"
    
    def on_start(self):
        """Инициализация пользователя"""
        self.token = None
        self.headers = {}
        self.created_codes = []
    
    @task(3)
    def create_short_link(self):
        """Создание короткой ссылки (самая частая операция)"""
        url = generate_test_url()
        
        with self.client.post(
            "/api/links/shorten",
            json={"original_url": url},
            headers=self.headers,
            name="/api/links/shorten",
            catch_response=True  
        ) as response:
            if response.status_code in (200, 201):
                try:
                    data = response.json()
                    code = data.get("short_code") or data.get("code")
                    if code:
                        self.created_codes.append(code)
                        response.success()  
                    else:
                        response.failure("No code in response") 
                except Exception as e:
                    response.failure(f"JSON parse error: {e}")
            elif response.status_code == 422:
                # Валидация — это нормально, не считаем ошибкой
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")
    
    @task(2)
    def redirect_to_original(self):
        """Редирект по короткой ссылке"""

        if not self.created_codes:

            return
        
        code = random.choice(self.created_codes)
        
        with self.client.get(
            f"/api/links/{code}",
            allow_redirects=False, 
            headers=self.headers,
            name="/api/links/[code]",
            catch_response=True
        ) as response:

            if response.status_code in (302, 404):
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")
    
    @task(1)
    def get_link_stats(self):
        """Получение статистики (требует авторизации)"""
        if not self.created_codes:
            return  # Пропускаем, если нет кодов
        
        code = random.choice(self.created_codes)
        
        with self.client.get(
            f"/api/links/{code}/stats",
            headers=self.headers,
            name="/api/links/[code]/stats",
            catch_response=True
        ) as response:

            if response.status_code in (200, 401, 403, 404):
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")


class AdminUser(HttpUser):
    """Пользователь с правами администратора (опционально)"""
    
    wait_time = between(2, 5)
    host = "http://localhost:8000"
    
    @task
    def bulk_create_links(self):
        """Массовое создание ссылок (нагрузочный сценарий)"""
        for _ in range(5):
            url = generate_test_url()
            with self.client.post(
                "/api/links/shorten",
                json={"original_url": url},
                name="/api/links/shorten",
                catch_response=True
            ) as response:
                if response.status_code in (200, 201, 422):
                    response.success()
                else:
                    response.failure(f"Unexpected status: {response.status_code}")
            self.wait()