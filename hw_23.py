from bs4 import BeautifulSoup
import requests
import time
from collections import defaultdict
import json
from datetime import datetime


def get_user_diary(user_login, pages=5):
    data = []

    for i in range(1, pages + 1):
        try:
            if i == 1:
                url = f'https://letterboxd.com/{user_login}/films/diary/'
            else:
                url = f'https://letterboxd.com/{user_login}/films/diary/page/{i}/'

            response = requests.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            entries = soup.find_all('tr', class_='diary-entry-row')

            for entry in entries:
                try:
                    # Название фильма
                    film_td = entry.find('td', class_='td-film-details')
                    film_name = film_td.find('a').text.strip() if film_td else "Unknown"

                    # Год выпуска
                    release_td = entry.find('td', class_='td-released')
                    release_date = release_td.text.strip() if release_td else "Unknown"

                    # Оценка пользователя
                    rating_td = entry.find('td', class_='td-rating')
                    if rating_td:
                        rating_span = rating_td.find('span', class_='rating')
                        rating = rating_span.text.strip() if rating_span else 'No rating'
                    else:
                        rating = 'No rating'

                    # Дата просмотра
                    date_td = entry.find('td', class_='td-day diary-day center')
                    watch_date = date_td.text.strip() if date_td else "Unknown"

                    data.append({
                        'film_name': film_name,
                        'release_date': release_date,
                        'rating': rating,
                        'watch_date': watch_date
                    })
                except Exception as e:
                    print(f"Error processing entry: {e}")
                    continue

            print(f"Processed page {i}, total films: {len(data)}")
            time.sleep(2)  # Вежливая задержка между запросами

        except Exception as e:
            print(f"Error processing page {i}: {e}")
            continue

    return data


def get_top_films_by_year(data, year):
    year_films = defaultdict(list)

    for film in data:
        try:
            film_year = film['release_date']
            if film_year.isdigit() and len(film_year) == 4:
                film_year = int(film_year)
                try:
                    # Преобразуем рейтинг в числовой формат
                    rating_str = film['rating']
                    if rating_str == 'No rating':
                        rating = 0
                    elif rating_str.startswith('★'):
                        rating = len(rating_str)
                    elif rating_str.startswith('½'):
                        rating = 0.5
                    else:
                        rating = float(rating_str)
                except:
                    rating = 0

                year_films[film_year].append({
                    'film_name': film['film_name'],
                    'rating': rating,
                    'watch_date': film['watch_date']
                })
        except:
            continue

    films = year_films.get(year, [])
    films.sort(key=lambda x: x['rating'], reverse=True)

    return films[:10]


def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Data saved to {filename}")


def main():
    user_login = input("Enter Letterboxd username: ")
    pages = int(input("How many pages to scan (1-10 recommended): "))

    print(f"Getting diary data for {user_login}...")
    data = get_user_diary(user_login, pages)

    if not data:
        print("No films found. Check username or try again later.")
        return

    # Генерируем имя файла с текущей датой
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = f"letterboxd_{user_login}_{timestamp}.json"
    save_to_json(data, json_filename)

    print(f"\nSuccessfully collected data for {len(data)} films.")

    while True:
        year = input("\nEnter year to get top films (or 'q' to quit): ")
        if year.lower() == 'q':
            break

        try:
            year = int(year)
            top_films = get_top_films_by_year(data, year)

            if not top_films:
                print(f"No films found for year {year}")
            else:
                print(f"\nTop 10 films for {year}:")
                for i, film in enumerate(top_films, 1):
                    print(f"{i}. {film['film_name']} - Rating: {film['rating']} - Watched: {film['watch_date']}")

                # Сохраняем топ фильмов в отдельный JSON
                top_filename = f"top_{year}_films_{user_login}.json"
                save_to_json(top_films, top_filename)
        except ValueError:
            print("Please enter a valid year (e.g. 1999)")


if __name__ == "__main__":
    main()