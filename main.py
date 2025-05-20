import requests
import json
import tkinter as tk
from tkinter import filedialog
import base64
import mimetypes
import os
from urllib.parse import quote_plus

TEXT_MODELS_URL = "https://text.pollinations.ai/models"
IMAGE_MODELS_URL = "https://image.pollinations.ai/models"
TEXT_GENERATION_OPENAI_URL = "https://text.pollinations.ai/openai" 
IMAGE_GENERATION_BASE_URL = "https://image.pollinations.ai/prompt/"

def fetch_models(url):
    """Получает список моделей с указанного URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе моделей: {e}")
        return None

def select_model_from_list(models_data, model_type="text"):
    """Позволяет пользователю выбрать модель из списка."""
    if not models_data:
        print("Список моделей пуст или не удалось загрузить.")
        return None

    print(f"\nДоступные модели для {model_type}:")
    if model_type == "text":
        for i, model in enumerate(models_data):
            print(f"{i + 1}. {model.get('name', 'N/A')} - {model.get('description', 'N/A')}")
    elif model_type == "image":
        for i, model_name in enumerate(models_data):
            print(f"{i + 1}. {model_name}")

    while True:
        try:
            choice = int(input("Выберите номер модели: ")) - 1
            if 0 <= choice < len(models_data):
                return models_data[choice]
            else:
                print("Неверный номер. Пожалуйста, попробуйте снова.")
        except ValueError:
            print("Неверный ввод. Пожалуйста, введите число.")

def get_image_path_gui():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Выберите фотографию",
        filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.bmp *.webp"), ("All files", "*.*")]
    )
    root.destroy()
    return file_path

def encode_image_to_base64(image_path):
    """Кодирует изображение в base64 строку."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Ошибка при кодировании изображения: {e}")
        return None

# --- Generation Functions ---
def generate_text_with_model(selected_model_details):
    """Генерация текста с использованием выбранной модели."""
    if not selected_model_details:
        return

    model_name = selected_model_details.get("name")
    print(f"\nВыбрана модель для текста: {model_name} ({selected_model_details.get('description')})")

    while True:
        prompt = input("Введите ваш текстовый запрос (или 'q' для выхода из этой модели): ")
        if prompt.lower() == 'q':
            break

        image_path = None
        image_base64 = None
        mime_type = None
        supports_images = "image" in selected_model_details.get("input_modalities", [])

        if supports_images:
            add_image_choice = input("Добавить фотографию к запросу? (да/нет): ").strip().lower()
            if add_image_choice == 'да':
                image_path = get_image_path_gui()
                if image_path:
                    print(f"Выбрана фотография: {image_path}")
                    image_base64 = encode_image_to_base64(image_path)
                    if image_base64:
                        mime_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"
                    else:
                        print("Не удалось обработать изображение.")
                else:
                    print("Фотография не выбрана.")

        messages = []
        if image_base64 and mime_type:
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_base64}"}}
                ]
            })
        else:
            messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model_name,
            "messages": messages
        }

        print("\nОтправка запроса...")
        try:
            response = requests.post(TEXT_GENERATION_OPENAI_URL, json=payload, headers={"Content-Type": "application/json"})
            response.raise_for_status()
            api_response = response.json()

            if api_response.get("choices"):
                generated_text = api_response["choices"][0].get("message", {}).get("content")
                print("\nОтвет модели:")
                print(generated_text)
            else:
                print("Не удалось получить сгенерированный текст.")
                print("Ответ API:", api_response)

        except requests.exceptions.RequestException as e:
            print(f"Ошибка при отправке запроса: {e}")
        except json.JSONDecodeError:
            print("Ошибка декодирования JSON. Ответ:", response.text)
        print("-" * 30)

def generate_image_with_model(selected_image_model_name):
    """Генерация изображения с использованием выбранной модели."""
    if not selected_image_model_name:
        return

    print(f"\nВыбрана модель для изображений: {selected_image_model_name}")

    while True:
        prompt = input("Введите ваш запрос для генерации изображения (или 'q' для выхода из этой модели): ")
        if prompt.lower() == 'q':
            break

        encoded_prompt = quote_plus(prompt)
        request_url = f"{IMAGE_GENERATION_BASE_URL}{encoded_prompt}?model={selected_image_model_name}"
        print(f"\nОтправка запроса на: {request_url}")

        try:
            response = requests.get(request_url, stream=True)
            response.raise_for_status()

            filename = f"generated_image_{selected_image_model_name}_{prompt[:20].replace(' ', '_')}.png"
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"Изображение сохранено как: {filename}")
            print(f"Полный путь: {os.path.abspath(filename)}")

        except requests.exceptions.RequestException as e:
            print(f"Ошибка при генерации изображения: {e}")
        print("-" * 30)

# --- Main Script ---
def main():
    print("Добро пожаловать в Pollinations.ai API клиент!")

    while True:
        print("\nКуда вас направить?")
        print("1. Генерация текста")
        print("2. Генерация фотографии")
        print("3. Выход")

        choice = input("Ваш выбор: ").strip()

        if choice == '1':
            print("\nЗагрузка моделей для текста...")
            text_models = fetch_models(TEXT_MODELS_URL)
            if text_models:
                selected_text_model_details = select_model_from_list(text_models, "text")
                if selected_text_model_details:
                    generate_text_with_model(selected_text_model_details)
            else:
                print("Не удалось загрузить текстовые модели.")

        elif choice == '2':
            print("\nЗагрузка моделей для изображений...")
            image_models = fetch_models(IMAGE_MODELS_URL)
            if image_models:
                selected_image_model_name = select_model_from_list(image_models, "image")
                if selected_image_model_name:
                    generate_image_with_model(selected_image_model_name)
            else:
                print("Не удалось загрузить модели изображений.")

        elif choice == '3':
            print("До свидания!")
            break
        else:
            print("Неверный выбор. Попробуйте снова.")

if __name__ == "__main__":
    main()
