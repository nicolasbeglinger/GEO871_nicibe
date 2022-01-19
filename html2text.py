from urllib.request import urlopen
from bs4 import BeautifulSoup

# from https://stackoverflow.com/questions/328356/extracting-text-from-html-file-using-python


def html2text(url: str, only_alpha: bool = True) -> str:
    """Takes a url and outputs the text

    Args:
        url (str): url of the website
        only_alpha (bool, optional): whether only alphabetic characters should be included into the 
        text. Defaults to True.

    Returns:
        str: string containing the text of the website
    """

    html = urlopen(url).read()
    soup = BeautifulSoup(html, features="html.parser")

    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract()    # rip it out

    # get text
    text = soup.get_text()

    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())

    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    text = ' '.join(chunk for chunk in chunks if chunk)

    if only_alpha:
        lyst = [".", ","]

        # text = "".join([letter for letter in text if letter.isalpha() or letter == ' '])
        text_only_alpha = ''
        for letter in text:
            if letter not in lyst:
                text_only_alpha += letter

            # if i % 10 == 0:
            #     print(i)

        return text_only_alpha

    return text


if __name__ == "__main__":
    print(html2text(
        url="https://www.theguardian.com/global-development/2021/dec/21/uk-accused-of-abandoning-\
            worlds-poor-as-aid-turned-into-colonial-investment",
        only_alpha=True))
