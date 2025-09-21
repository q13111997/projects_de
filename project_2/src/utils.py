from bs4 import BeautifulSoup

# parse description của product và nối với nhau bằng 1 khoảng trắng " "
def clean_description(html_text):
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    return " ".join(text.split())