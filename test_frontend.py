"""Test FastEat AI frontend end-to-end."""

from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('http://127.0.0.1:5500')
        page.wait_for_load_state('networkidle')

        print("=== Page loaded ===")
        page.screenshot(path='frontend_test.png', full_page=True)
        print("Screenshot saved to frontend_test.png")

        print("=== Testing navigation ===")
        page.click('text=Create My Recipe')
        print("Navigated to generator section")

        print("=== Testing file upload ===")
        with open('D:/ACL_Agent/real_food.jpg', 'rb') as f:
            file = p.sync_playwright.request.post(
                'http://127.0.0.1:5500/',
                files={'image': f}
            )

        file_input = page.locator('#fileInput')
        file_input.set_input_files('D:/ACL_Agent/real_food.jpg')
        print("File uploaded")

        page.wait_for_timeout(1000)

        print("=== Checking preview ===")
        preview_area = page.locator('#previewArea')
        if preview_area.is_visible():
            print("✓ Preview area is visible")
            preview_image = page.locator('#previewImage')
            print(f"✓ Preview image src: {preview_image.get_attribute('src')[:50]}...")
        else:
            print("✗ Preview area not visible")

        print("=== Clicking Generate Recipe ===")
        generate_btn = page.locator('#generateBtn')
        if generate_btn.is_enabled():
            generate_btn.click()
            print("✓ Generate button clicked")
        else:
            print("✗ Generate button not enabled")

        print("=== Waiting for loading state ===")
        page.wait_for_selector('#loadingState', state='visible')
        print("✓ Loading state appeared")

        print("=== Waiting for recipe result ===")
        try:
            page.wait_for_selector('#recipe-result.visible', timeout=180000)
            print("✓ Recipe result appeared")
            page.screenshot(path='frontend_recipe_result.png', full_page=True)
            print("Screenshot saved to frontend_recipe_result.png")

            print("=== Checking recipe structure ===")
            title = page.locator('#recipeTitle').text_content()
            print(f"Title: {title}")

            ingredients = page.locator('.ingredient-name').all()
            print(f"Ingredients found: {len(ingredients)}")

            instructions = page.locator('.step-text').all()
            print(f"Instructions found: {len(instructions)}")

        except Exception as e:
            print(f"✗ Recipe result not found: {e}")

        print("=== Closing browser ===")
        browser.close()

if __name__ == '__main__':
    main()
