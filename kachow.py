from datetime import date
from dateutil.relativedelta import relativedelta
from lxml import etree


def uptime():
    birthday = date(2003, 9, 23)
    today = date.today()
    diff = relativedelta(today, birthday)
    return f"{diff.years} years, {diff.months} months, {diff.days} days"


def update_dots(root, total_width=47):
    ns = {"svg": "http://www.w3.org/2000/svg"}
    for tspan in root.findall(".//svg:tspan", ns):
        if tspan.get("id") == "dots":
            prev_tspan = tspan.getprevious()
            next_tspan = tspan.getnext()

            prev_text = prev_tspan.text if prev_tspan is not None else ""
            next_text = next_tspan.text if next_tspan is not None else ""

            used_width = len(prev_text) + len(next_text) + 2
            dots_needed = max(1, total_width - used_width)
            tspan.text = " " + "." * dots_needed + " "


def update_svg_element(root, id, value):
    element = root.find(f".//*[@id='{id}']")
    if element is not None:
        element.text = value


def update_svg_file(filepath):
    with open(filepath, "r") as f:
        content = f.read()

    root = etree.fromstring(content)

    current_uptime = uptime()
    update_svg_element(root, "uptime", current_uptime)

    update_dots(root)

    with open(filepath, "w") as f:
        f.write(etree.tostring(root, encoding="unicode", pretty_print=True))


if __name__ == "__main__":
    update_svg_file("dark.svg")
    update_svg_file("light.svg")
