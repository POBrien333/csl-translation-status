import requests
import xml.etree.ElementTree as ET
import re
import os
from typing import Dict, List, Tuple
from datetime import datetime

# Define the base URL for fetching locale XML
BASE_URL = "https://raw.githubusercontent.com/citation-style-language/locales/master/locales-{}.xml"

# Simple mapping for language codes to human-readable names (extensible)
LANG_NAMES = {
    "af-ZA": "Afrikaans", "ar": "Arabic", "bal-PK": "Balochi (Pakistan)", "bg-BG": "Bulgarian",
    "brh-PK": "Brahui", "ca-AD": "Catalan", "cs-CZ": "Czech", "cy-GB": "Welsh",
    "da-DK": "Danish", "de-DE": "German (Germany)", "el-GR": "Greek", "en-US": "English (US)",
    "es-ES": "Spanish (Spain)", "et-EE": "Estonian", "eu": "Basque", "fa-IR": "Persian",
    "fi-FI": "Finnish", "fr-FR": "French (France)", "gl-ES": "Galician (Spain)", "he-IL": "Hebrew",
    "hi-IN": "Hindi", "hr-HR": "Croatian", "hu-HU": "Hungarian", "id-ID": "Indonesian",
    "is-IS": "Icelandic", "it-IT": "Italian", "ja-JP": "Japanese", "km-KH": "Khmer",
    "ko-KR": "Korean", "la": "Latin", "lij-IT": "Ligurian", "lt-LT": "Lithuanian",
    "lv-LV": "Latvian", "mn-MN": "Mongolian", "ms-MY": "Malay", "nb-NO": "Norwegian (Bokmål)",
    "nl-NL": "Dutch", "nn-NO": "Norwegian (Nynorsk)", "pa-PK": "Punjabi (Shahmukhi)",
    "pl-PL": "Polish", "pt-PT": "Portuguese (Portugal)", "ro-RO": "Romanian", "ru-RU": "Russian",
    "sk-SK": "Slovak", "sl-SI": "Slovenian", "sr-RS": "Serbian", "sv-SE": "Swedish",
    "th-TH": "Thai", "tr-TR": "Turkish", "uk-UA": "Ukrainian", "vi-VN": "Vietnamese",
    "zh-CN": "Chinese (PRC)", "de-AT": "German (Austria)", "de-CH": "German (Switzerland)",
    "en-GB": "English (UK)", "es-CL": "Spanish (Chile)", "es-MX": "Spanish (Mexico)",
    "fr-CA": "French (Canada)", "pt-BR": "Portuguese (Brazil)", "zh-TW": "Chinese (Taiwan)"
}

def fetch_locale_codes() -> List[str]:
    """Fetch the list of locale codes dynamically from GitHub repo."""
    api_url = "https://api.github.com/repos/citation-style-language/locales/contents"
    params = {"ref": "master"}
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        files = response.json()
        pattern = re.compile(r'^locales-([a-zA-Z0-9\-]+)\.xml$')
        locale_codes = []
        for file_info in files:
            if file_info["type"] == "file":
                match = pattern.match(file_info["name"])
                if match:
                    locale_codes.append(match.group(1))
        print(f"Found {len(locale_codes)} locale files via GitHub API.")
        return sorted(set(locale_codes))
    except requests.exceptions.RequestException as e:
        print(f"Error fetching locale list: {e}")
        return []

def get_language_name(lang_code: str) -> str:
    return LANG_NAMES.get(lang_code, lang_code)

def fetch_xml_content(lang_code: str) -> str | None:
    url = BASE_URL.format(lang_code)
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {lang_code}: {e}")
        return None

def parse_locale_terms(xml_string: str) -> Dict[Tuple[str, str], str | Tuple[str, str]]:
    """Parse XML string and return dict of terms."""
    if not xml_string:
        return {}
    terms = {}
    try:
        root = ET.fromstring(xml_string)
        namespace = '{http://purl.org/net/xbiblio/csl}'
        term_elements = root.findall(f'{namespace}terms/{namespace}term')
        for term in term_elements:
            name = term.get('name', '')
            form = term.get('form', '')
            single_tag = term.find(f'{namespace}single')
            multiple_tag = term.find(f'{namespace}multiple')
            if single_tag is not None and multiple_tag is not None:
                single_text = single_tag.text.strip() if single_tag.text else ''
                multiple_text = multiple_tag.text.strip() if multiple_tag.text else ''
                terms[(name, form)] = (single_text, multiple_text)
            else:
                terms[(name, form)] = term.text.strip() if term.text else ''
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        return {}
    return terms

def generate_locale_page(lang_code: str, lang_name: str, untranslated_terms: List[Dict], total_terms: int):
    """Generate per-locale HTML page."""
    os.makedirs("docs/locales", exist_ok=True)
    last_updated = datetime.now().strftime("%B %d, %Y")
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Untranslated Terms - {lang_name} ({lang_code})</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
h1, p {{ text-align: center; }}
table {{ max-width: 800px; width: 100%; border-collapse: collapse; margin: 20px auto; }}
th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
th {{ background-color: #2d98e0; color: white; }}
tr:nth-child(even) {{ background-color: #f9f9f9; }}
tr:hover {{ background-color: #f5f5f5; }}
.updated {{ font-size: 0.9em; color: #888; text-align: center; }}
</style>
</head>
<body>
<h1>Untranslated Terms for {lang_name} ({lang_code})</h1>
<p>Showing {len(untranslated_terms)} untranslated terms out of {total_terms} total terms. Last updated: {last_updated}.</p>
<p><a href="../index.html">Back to Translation Status</a></p>
<table>
<thead><tr><th>Term Name</th><th>Form</th><th>English Text</th></tr></thead>
<tbody>
"""
    for term in untranslated_terms:
        name, form = term['key']
        value = term['value']
        if isinstance(value, tuple):
            value_text = f"Single: {value[0]}<br>Multiple: {value[1]}"
        else:
            value_text = value
        html_content += f"<tr><td>{name}</td><td>{form or '-'}</td><td>{value_text}</td></tr>\n"
    html_content += """</tbody></table>
<p class="updated">Data fetched from <a href="https://github.com/citation-style-language/locales">CSL locales repo</a>.</p>
</body></html>"""
    with open(f"docs/locales/locale_{lang_code}.html", "w", encoding="utf-8") as f:
        f.write(html_content)

def main():
    locale_codes = fetch_locale_codes()
    if not locale_codes or "en-US" not in locale_codes:
        print("No locales or en-US missing. Exiting.")
        return
    english_xml = fetch_xml_content("en-US")
    english_terms = parse_locale_terms(english_xml)
    total_terms = len(english_terms)
    results = []
    for lang_code in locale_codes:
        if lang_code == "en-US":
            continue
        lang_name = get_language_name(lang_code)
        current_xml = fetch_xml_content(lang_code)
        if not current_xml:
            continue
        current_terms = parse_locale_terms(current_xml)
        untranslated_terms = []
        untranslated_count = 0
        for term_key, english_value in english_terms.items():
            current_value = current_terms.get(term_key)
            if isinstance(english_value, tuple):
                eng_str = f"{english_value[0]}|{english_value[1]}"
            else:
                eng_str = str(english_value)
            if isinstance(current_value, tuple):
                curr_str = f"{current_value[0]}|{current_value[1]}"
            else:
                curr_str = str(current_value)
            if curr_str == eng_str:
                untranslated_terms.append({"key": term_key, "value": english_value})
                untranslated_count += 1
        translated_count = total_terms - untranslated_count
        percentage = (translated_count / total_terms) * 100 if total_terms else 0
        results.append({
            "language": lang_name,
            "lang_code": lang_code,
            "translated_count": translated_count,
            "untranslated_count": untranslated_count,
            "percentage": percentage,
            "untranslated_terms": untranslated_terms
        })
        generate_locale_page(lang_code, lang_name, untranslated_terms, total_terms)
    results.sort(key=lambda x: x["percentage"], reverse=True)
    last_updated = datetime.now().strftime("%B %d, %Y")
    os.makedirs("docs", exist_ok=True)
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CSL Locale Translation Status</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
h1, p {{ text-align: center; }}
table {{ max-width: 800px; width: 100%; border-collapse: collapse; margin: 20px auto; }}
th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
th {{ background-color: #2d98e0; color: white; }}
tr:nth-child(even) {{ background-color: #f9f9f9; }}
tr:hover {{ background-color: #f5f5f5; }}
.updated {{ font-size: 0.9em; color: #888; text-align: center; }}
</style>
</head>
<body>
<h1>CSL Locale Translation Status</h1>
<p>Generated dynamically from the official <a href="https://github.com/citation-style-language/locales">CSL locales repository</a>.</p>
<p>Last updated: {last_updated}</p>
<p class="updated">Total locales analyzed: {len(results)}</p>
<table>
<thead><tr><th>Language</th><th>Translated Terms</th><th>Untranslated Terms</th><th>Translation %</th></tr></thead>
<tbody>
"""
    for res in results:
        html_content += f"<tr><td><a href='locales/locale_{res['lang_code']}.html'>{res['language']} ({res['lang_code']})</a></td><td>{res['translated_count']}</td><td>{res['untranslated_count']}</td><td>{res['percentage']:.1f}%</td></tr>\n"
    html_content += """</tbody></table>
<p class="updated">Run the script to refresh data.</p>
</body></html>"""
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"HTML file 'docs/index.html' generated with {len(results)} locales.")

if __name__ == "__main__":
    main()
