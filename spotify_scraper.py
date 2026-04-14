import asyncio
import os
import sys
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        # Use an absolute path for the user_data directory
        base_path = os.path.dirname(os.path.abspath(__file__))
        user_data_dir = os.path.join(base_path, "user_data")
        
        if not os.path.exists(user_data_dir):
            os.makedirs(user_data_dir)
            print(f"Created user data directory at: {user_data_dir}")

        print("Launching browser with persistent context...")
        # Note: Persistent context saves cookies, local storage, etc.
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            args=["--start-maximized"]
        )
        
        try:
            page = context.pages[0] if context.pages else await context.new_page()
            
            # Target URL
            url = "https://developer.spotify.com/documentation/web-api/reference/get-an-artist"
            print(f"Navigating to {url}...")
            
            # Use a longer timeout for navigation in case of slow connections
            try:
                await page.goto(url, wait_until="load", timeout=60000)
            except Exception as e:
                print(f"Initial navigation warning: {e}. Checking if we are on a login page...")

            # Selectors
            input_selector = 'input.e-10202-form-input.hUEbal'
            
            # 1. Login/Navigation check loop
            print("Monitoring page for Artist ID input field...")
            while True:
                try:
                    # Check if the input field is present
                    if await page.query_selector(input_selector):
                        print("✅ Detected documentation console. Proceeding...")
                        break
                    
                    # If not, check if we are on a login page or elsewhere
                    current_url = page.url
                    if "accounts.spotify.com" in current_url:
                        print(f"Status: Waiting for login at {current_url}...", end="\r")
                    else:
                        print(f"Status: On unexpected page {current_url}. Waiting for redirect...", end="\r")
                        
                except Exception as e:
                    print(f"Warning during monitor loop: {e}")
                
                await asyncio.sleep(2)

            # 2. Input artist ID
            artist_id = "0tB33cNAVw1H2enMHpgFiP"
            await page.wait_for_selector(input_selector, state="visible")
            await page.fill(input_selector, "")
            await page.fill(input_selector, artist_id)
            print(f"Filled Artist ID: {artist_id}")

            # --- Retry Loop for "Try it" ---
            max_retries = 3
            success = False
            response_selector = 'pre.sc-dcdedfe6-0.ePqgwR'
            button_selector = 'button:has-text("Try it")'

            for attempt in range(max_retries):
                print(f"\nAttempt {attempt + 1} of {max_retries}...")
                
                # 3. Press the "Try it" button
                await page.click(button_selector)
                print("Clicked 'Try it' button.")

                # 4. Wait 1 second (as requested)
                print("Waiting 1 second for response...")
                await asyncio.sleep(1)

                # 5. Get and validate the data response
                print("Checking response...")
                try:
                    # Wait for the specific response container
                    await page.wait_for_selector(response_selector, state='visible', timeout=10000)
                    response_text = await page.inner_text(response_selector)
                    
                    # Check for 502 or Error
                    if "502" in response_text or "error" in response_text.lower():
                        print(f"⚠️ Response contains 502 or Error. Retrying in 2 seconds...")
                        await asyncio.sleep(2)
                        continue
                    
                    # If we reach here, it's a valid response
                    print("\n" + "="*50)
                    print("SUCCESS: RESPONSE DATA EXTRACTED")
                    print("="*50)
                    print(response_text[:500] + "..." if len(response_text) > 500 else response_text)
                    print("="*50 + "\n")
                    
                    with open("response.json", "w", encoding="utf-8") as f:
                        f.write(response_text)
                    print("Successfully saved to response.json")
                    success = True
                    break
                        
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed to find response: {e}")
                    if attempt < max_retries - 1:
                        print("Retrying...")
                        await asyncio.sleep(2)

            if not success:
                print("❌ Failed to get a valid response after multiple attempts.")
                print("Trying to grab any 'pre' tag content as a last resort...")
                all_pres = await page.query_selector_all('pre')
                if all_pres:
                    text = await all_pres[-1].inner_text()
                    print(f"Last resort text: {text[:100]}...")

        except Exception as e:
            print(f"\n❌ SCRIPT ERROR: {e}")
        
        finally:
            print("\n" + "!"*50)
            print("Browser will stay open so you can inspect the result.")
            print("Press ENTER in this window to close everything.")
            print("!"*50)
            # Use sys.stdin.readline to handle input better in some terminals
            await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            await context.close()

if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nScript stopped by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
