import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import time
import sys

ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"

def clean_text(s):
    return re.sub(r"\s+", " ", s or "").strip()

def cite_key(authors, year, arxiv_id):
    first = authors[0].split()[-1] if authors else "arxiv"
    return re.sub(r"[^A-Za-z0-9]", "", f"{first}{year}{arxiv_id.split('.')[-1]}")

def arxiv_to_bibtex(arxiv_id: str) -> str:
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({
        "id_list": arxiv_id,
        "max_results": 1,
    })

    xml = urllib.request.urlopen(url, timeout=20).read()
    root = ET.fromstring(xml)
    entry = root.find(f"{ATOM}entry")
    if entry is None:
        raise ValueError("No arXiv entry found")

    title = clean_text(entry.findtext(f"{ATOM}title"))
    authors = [
        clean_text(a.findtext(f"{ATOM}name"))
        for a in entry.findall(f"{ATOM}author")
    ]

    published = entry.findtext(f"{ATOM}published") or ""
    year = published[:4] if published else ""

    abs_url = clean_text(entry.findtext(f"{ATOM}id"))
    eprint = abs_url.rsplit("/", 1)[-1]
    eprint_no_version = re.sub(r"v\d+$", "", eprint)

    primary = entry.find(f"{ARXIV}primary_category")
    primary_class = primary.attrib.get("term", "") if primary is not None else ""

    doi = clean_text(entry.findtext(f"{ARXIV}doi"))
    journal_ref = clean_text(entry.findtext(f"{ARXIV}journal_ref"))

    key = cite_key(authors, year, eprint_no_version)

    fields = {
        "title": title,
        "author": " and ".join(authors),
        "year": year,
        "eprint": eprint_no_version,
        "archivePrefix": "arXiv",
        "primaryClass": primary_class,
        "url": f"https://arxiv.org/abs/{eprint_no_version}",
    }

    if doi:
        fields["doi"] = doi
    if journal_ref:
        fields["journal"] = journal_ref

    body = "\n".join(
        f"  {k} = {{{v}}},"
        for k, v in fields.items()
        if v
    )

    return f"@misc{{{key},\n{body}\n}}"

def get_all_arxiv_ids():
    """从 hybrid.bib 文件中提取所有 arXiv ID"""
    arxiv_ids = []
    try:
        with open("hybrid.bib", "r", encoding="utf-8") as f:
            content = f.read()
            # 匹配 eprint = {数字.数字} 格式
            matches = re.findall(r'eprint\s*=\s*{(\d+\.\d+)}', content)
            arxiv_ids = list(set(matches))  # 去重
    except FileNotFoundError:
        print("警告: hybrid.bib 文件未找到，使用默认的 arXiv ID 列表")
        arxiv_ids = ["2310.05737", "2405.09818", "2408.11039", "2408.12528", "2307.08041", 
                    "2310.01218", "2309.04669", "2404.14396", "2505.05422", "2506.15564",
                    "2510.06590", "2412.15188", "2501.17811", "2501.12327", "2503.13436",
                    "2504.02949", "2505.14682", "2505.05472", "2505.14683", "2506.18871",
                    "2506.23044", "2506.10395", "2506.03147", "2508.03320", "2509.04548",
                    "2510.22946", "2511.14760", "2504.01934", "2504.04423", "2512.04810",
                    "2503.06764"]
    return arxiv_ids

def main():
    arxiv_ids = get_all_arxiv_ids()
    print(f"找到 {len(arxiv_ids)} 个 arXiv ID，开始处理...")
    
    for i, arxiv_id in enumerate(arxiv_ids):
        try:
            print(f"处理第 {i+1}/{len(arxiv_ids)} 个: {arxiv_id}")
            bibtex = arxiv_to_bibtex(arxiv_id)
            print(bibtex)
            print("-" * 80)
            
            # 如果不是最后一个，等待5秒
            if i < len(arxiv_ids) - 1:
                print("等待5秒...")
                time.sleep(5)
                
        except Exception as e:
            print(f"处理 {arxiv_id} 时出错: {e}")
            print("继续处理下一个...")
            print("-" * 80)

if __name__ == "__main__":
    main()