import re

from bs4 import BeautifulSoup


def parse_html_content(html_text: str, length_limit: int = 500) -> str:
    """移除 html 內容的標籤，只留下純文字

    ------
    Parameters
    html_text `str`: 原始 html 內容
    length_limit `int`: 限制傳回字串的最大長度
    ------
    Returns
    `str`: 無 html 標籤的純文字
    """
    # 移除米哈遊自訂的時間標籤
    html_text = html_text.replace('&lt;t class="t_lc"&gt;', "")
    html_text = html_text.replace('&lt;t class="t_gl"&gt;', "")
    html_text = html_text.replace("&lt;/t&gt;", "")

    soup = BeautifulSoup(html_text, features="html.parser")
    url_pattern = re.compile(r"\(\'(https?://.*)\'\)")

    result = ""
    text_length = 0  # 用來統計已處理的文字長度
    for row in soup:
        if text_length > length_limit:
            return result + "..."

        if row.a is not None and (url := url_pattern.search(row.a["href"])):
            # 將連結轉換成 discord 格式
            result += f"[{row.text}]({url.group(1)})\n"
            text_length += len(row.text)
        elif row.img is not None:
            # 將圖片以連結顯示
            url = row.img["src"]
            result += f"[>>圖片<<]({url})\n"
        elif row.name == "div" and row.table is not None:
            # 將表格同一行內容以符號隔開
            for tr in row.find_all("tr"):
                for td in tr.find_all("td"):
                    result += "· " + td.text + " "
                    text_length += len(td.text)
                result += "\n"
        elif row.name == "ol":
            # 將有序項目每一行開頭加入數字
            for i, li in enumerate(row.find_all("li")):
                result += f"{i+1}. {li.text}\n"
                text_length += len(li.text)
        elif row.name == "ul":  # 無序項目
            # 將無序項目每一行開頭加入符號
            for li in row.find_all("li"):
                result += "· " + li.text + "\n"
                text_length += len(li.text)
        else:  # 一般內容
            text = row.text.strip() + "\n"
            result += text
            text_length += len(text)

    return result
