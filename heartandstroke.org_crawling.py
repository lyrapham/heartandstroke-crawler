import os
import json
import time
from selenium import webdriver
from bs4 import BeautifulSoup

# Test thử link đầu tiên --> vẫn sai
main_links = [
    "https://www.heartandstroke.ca/heart-disease"
    # "https://www.heartandstroke.ca/stroke",
    # "https://www.heartandstroke.ca/healthy-living",
    # "https://www.heartandstroke.ca/what-we-do",
    # "https://www.heartandstroke.ca/women"
]

output_file = "heartandstroke.json"

# Load if file already had content
def load_existing_articles(output_file):
    if os.path.exists(output_file):
        with open(output_file, "r") as file:
            articles = json.load(file)
    else:
        articles = []
    return articles

# Save to JSON
def save_articles_to_json(articles, output_file):
    with open(output_file, "w") as file:
        json.dump(articles, file, indent=4)

def initialize_driver():
    return webdriver.Chrome()


def extract_articles(soup, existing_urls):
    articles = []

    # Extract articles with named classes
    for link in soup.select("a.site-header__link.site-header__link--second-level, a.media-cards__link, a.sl-card__info-link, a.sl-tile, a.links__link, a.resource-block__item-link"):
        article_url = link.get('href')
        title = link.get("data-gtm-item-name", "Angina")

        # If title is not in <a> --> search span & h3
        if not title:
            span_title = link.select_one("span.media-cards__item-title, h3.resource-block__item-title")
            title = span_title.get_text(strip=True) if span_title else link.get_text(strip=True)

        # Make sure no duplication
        if article_url and article_url not in existing_urls:
            articles.append({
                "title": title,
                "url": article_url,
                "second level links": []
            })
            existing_urls.add(article_url)

    return articles

# Load 1st links then extract 2nd articles
def extract_second_level_links(driver, article):
    second_level_links = []
    driver.get(article["url"])
    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    for link in soup.select("a"):
        url = link.get("href")

        # Put domain as requirement
        if url and url.startswith("https://www.heartandstroke.ca/") and url != article["url"]:
            title = link.get_text(strip=True)
            if title and url:
                second_level_links.append({
                    "title": title,
                    "url": url
                })

    return second_level_links

def crawl_main_link(driver, link, existing_urls):
    print(f"Processing link: {link}")
    driver.get(link)
    time.sleep(2) 

    last_page_source = ""
    all_articles = []

    while True:
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Check last page to quit
        if driver.page_source == last_page_source:
            print("Reached last page! Finished!")
            break
        last_page_source = driver.page_source
        articles = extract_articles(soup, existing_urls)
        all_articles.extend(articles)

    print(f"Done crawling for {link}")
    return all_articles

def main():
    # Load existing articles if the file exists
    articles = load_existing_articles(output_file)
    existing_urls = set(article["url"] for article in articles)
    driver = initialize_driver()

    try:

        for main_link in main_links:
            # Get 1st-level article
            new_articles = crawl_main_link(driver, main_link, existing_urls)
            for article in new_articles:
                # Get 2nd-level article
                article["second level links"] = extract_second_level_links(driver, article)
                articles.append(article)
    finally:
        # Close the browser
        driver.quit()

    # Save file
    save_articles_to_json(articles, output_file)
    print("Process is done! Check JSON pls. ")

if __name__ == "__main__":
    main()
