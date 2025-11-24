from playwright.sync_api import sync_playwright
import os

def generate_icon():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1024, 'height': 1024})
        
        # Load local HTML file
        file_path = os.path.abspath("icon_design.html")
        page.goto(f"file://{file_path}")
        
        # Screenshot
        page.screenshot(path="app_icon.png", omit_background=True)
        print("Icon generated: app_icon.png")
        browser.close()

if __name__ == "__main__":
    generate_icon()
