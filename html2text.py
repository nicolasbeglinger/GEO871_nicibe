from urllib.request import urlopen
from bs4 import BeautifulSoup

# from https://stackoverflow.com/questions/328356/extracting-text-from-html-file-using-python

def html2text(url: str, onlyAlpha: bool=True) -> str:

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

    if onlyAlpha:
        lyst = [".", ","]

        # text = "".join([letter for letter in text if letter.isalpha() or letter == ' '])
        textOnlyAlpha = ''
        for i, letter in enumerate(text):
            if letter not in lyst:
                textOnlyAlpha += letter
            
            # if i % 10 == 0:
            #     print(i)

        return textOnlyAlpha
    
    return text

if __name__ == "__main__":
    print(html2text(
        url="https://www.theguardian.com/global-development/2021/dec/21/uk-accused-of-abandoning-worlds-poor-as-aid-turned-into-colonial-investment",
        onlyAlpha=True))
