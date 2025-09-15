import os
import polib
import glob
from datetime import datetime


def generate_locale_page(lang_code, lang_name, untranslated_terms, total_terms):
    """Generate a static HTML page for a specific locale with last updated date."""
    os.makedirs("docs/locales", exist_ok=True)

    last_updated = datetime.now().strftime("%B %d, %Y")

    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>{lang_name} Translation Report</title>
        <link rel="stylesheet" href="../style.css">
    </head>
    <body>
        <h1>{lang_name} ({lang_code}) Translation Report</h1>
        <p>Showing {untranslated_count} untranslated terms out of {total_count} total terms. 
        Last updated: {last_updated}.</p>
        <ul>
            {terms}
        </ul>
        <p><a href="../index.html">Back to Overview</a></p>
    </body>
    </html>
    """.format(
        lang_name=lang_name,
        lang_code=lang_code,
        untranslated_count=len(untranslated_terms),
        total_count=total_terms,
        last_updated=last_updated,
        terms="\n".join(f"<li>{term}</li>" for term in untranslated_terms)
    )

    with open(f"docs/locales/{lang_code}.html", "w", encoding="utf-8") as f:
        f.write(html_content)


def main():
    # 1. Prepare docs dir
    os.makedirs("docs", exist_ok=True)

    # 2. Find .po files
    po_files = glob.glob("locales/*/LC_MESSAGES/messages.po")

    results = []
    untranslated_details = {}

    # 3. Process each locale file
    for po_file in po_files:
        lang_code = po_file.split("/")[1]
        po = polib.pofile(po_file)

        total_terms = len(po)
        untranslated_terms = [entry.msgid for entry in po if not entry.msgstr]

        untranslated_count = len(untranslated_terms)
        completion = 100 - (untranslated_count / total_terms * 100)

        results.append((lang_code, completion, untranslated_count, total_terms))
        untranslated_details[lang_code] = (po.metadata.get("Language", lang_code),
                                           untranslated_terms,
                                           total_terms)

    # 4. Sort by completion %
    results.sort(key=lambda x: x[1], reverse=True)

    # 5. Get current date/time
    last_updated = datetime.now().strftime("%B %d, %Y")

    # 6. Generate overview index
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Translation Coverage Report</title>
        <link rel="stylesheet" href="style.css">
    </head>
    <body>
        <h1>Translation Coverage Overview</h1>
        <p>Generated dynamically from .po files. Last updated: {last_updated}.</p>
        <table>
            <tr>
                <th>Language Code</th>
                <th>Completion %</th>
                <th>Untranslated</th>
                <th>Total Terms</th>
                <th>Details</th>
            </tr>
            {rows}
        </table>
        <p class="updated">Total locales analyzed: {locale_count}</p>
    </body>
    </html>
    """.format(
        last_updated=last_updated,
        locale_count=len(results),
        rows="\n".join(
            "<tr><td>{}</td><td>{:.2f}%</td><td>{}</td><td>{}</td>"
            "<td><a href='locales/{}.html'>View</a></td></tr>".format(
                lang_code, completion, untranslated, total,
                lang_code
            ) for lang_code, completion, untranslated, total in results
        )
    )

    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    # 7. Generate locale-specific pages
    for lang_code, (lang_name, untranslated_terms, total_terms) in untranslated_details.items():
        generate_locale_page(lang_code, lang_name, untranslated_terms, total_terms)


if __name__ == "__main__":
    main()
