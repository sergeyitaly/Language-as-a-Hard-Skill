import requests
from bs4 import BeautifulSoup
from langdetect import detect
from collections import defaultdict
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import warnings
import plotly.graph_objects as go

# Suppress warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

def get_archived_html(website_url, timestamp):
    wayback_url = f"http://web.archive.org/web/{timestamp}/{website_url}"
    
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    try:
        response = session.get(wayback_url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.HTTPError as errh:
        if response.status_code == 404:
            print(f"Error 404: {wayback_url} not found.")
        else:
            print(f"HTTP Error: {errh}")
    except requests.exceptions.ConnectionError as errc:
        warnings.warn(f"Error Connecting: {errc}", RuntimeWarning)
    except requests.exceptions.Timeout as errt:
        print(f"Timeout Error: {errt}")
    except requests.exceptions.RequestException as err:
        print(f"An error occurred: {err}")
    return None

def analyze_language_percentage(websites, start_year, end_year):
    language_percentage_data = defaultdict(lambda: defaultdict(int))

    for website_name, website_url in websites.items():
        print(f"\nAnalyzing {website_name}...")

        for year in range(start_year, end_year + 1):
            for month in range(1, 13):  # Analyzing by months
                timestamp = f"{year}{month:02d}01"
                archived_html = get_archived_html(website_url, timestamp)

                if archived_html:
                    try:
                        soup = BeautifulSoup(archived_html, 'html.parser')
                        paragraphs = soup.find_all('p')
                        total_content_languages = 0
                        language_counts = defaultdict(int)

                        for paragraph in paragraphs:
                            text = paragraph.get_text()
                            if text.strip():
                                language = detect(text)
                                language_counts[language] += 1
                                total_content_languages += 1

                        for language, count in language_counts.items():
                            percentage = (count / total_content_languages) * 100 if total_content_languages > 0 else 0
                            language_percentage_data[website_name][(year, month, language)] = percentage

                    except Exception as e:
                        print(f"Error processing {website_url} at {timestamp}: {str(e)}")

    return language_percentage_data

def create_chart(language_percentage_data, output_file="language_chart.html"):
    fig = go.Figure()

    for website_name, language_data in language_percentage_data.items():
        for language in ['uk', 'ru', 'en']:
            x_values = []
            y_values = []

            for key in sorted(language_data.keys()):
                if key[2] == language and language_data[key] != 0:
                    x_values.append(f"{key[0]}-{key[1]:02d}")
                    y_values.append(language_data[key])

            if x_values and y_values:
                line_name = f"{website_name} ({language})"
                fig.add_trace(go.Scatter(
                    x=x_values,
                    y=y_values,
                    mode='lines+markers',
                    name=line_name
                ))

    fig.update_layout(
        title='Language Percentage Analysis in IT Opened Vacancies',
        xaxis_title='Year-Month',
        yaxis_title='Percentage',
        template='plotly_dark'
    )

    fig.write_html(output_file)
    print(f"Chart saved to {output_file}")

def main():
    websites = {
        'work.ua': 'https://work.ua/jobs-it/',
        'jobs.ua': 'https://jobs.ua/vacancy/it_web_specialists/',
        'djjini.co': 'https://djinni.co/jobs/'
        
    }
    start_year = 2022
    end_year = 2023

    language_percentage_data = analyze_language_percentage(websites, start_year, end_year)
    create_chart(language_percentage_data)

if __name__ == "__main__":
    main()
