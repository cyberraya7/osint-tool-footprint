#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
from colorama import init
import re
import phonenumbers
from googlesearch import search
import streamlit as st
import time

init(autoreset=True)

class UsernameOSINT:
    def __init__(self, username):
        self.username = username
        self.results = {}
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        self.phone_pattern = re.compile(r'\+?[1-9][0-9]{7,14}')

    def check_github(self):
        """Check GitHub profile"""
        try:
            response = requests.get(f"https://api.github.com/users/{self.username}", headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                return {
                    "exists": True,
                    "name": data.get("name"),
                    "bio": data.get("bio"),
                    "location": data.get("location"),
                    "public_repos": data.get("public_repos"),
                    "followers": data.get("followers"),
                    "following": data.get("following"),
                    "profile_url": data.get("html_url"),
                    "email": data.get("email")
                }
        except Exception as e:
            st.error(f"Error checking GitHub: {e}")
        return {"exists": False}

    def check_platform(self, url):
        """Check generic platform profile"""
        try:
            response = requests.get(url, headers=self.headers)
            return {"exists": response.status_code == 200}
        except Exception as e:
            st.error(f"Error checking platform: {e}")
            return {"exists": False}

    def search_web(self, search_query, pattern):
        """Generic web search for emails or phone numbers"""
        found_items = set()
        try:
            search_results = search(search_query, num_results=10)
            for url in search_results:
                try:
                    response = requests.get(url, headers=self.headers, timeout=5)
                    if response.status_code == 200:
                        items = pattern.findall(response.text)
                        found_items.update(items)
                except:
                    continue
        except Exception as e:
            st.error(f"Error searching web: {e}")
        return list(found_items)

    def search_emails(self):
        return self.search_web(f"{self.username} email contact", self.email_pattern)

    def search_whatsapp(self):
        found_numbers = self.search_web(f"{self.username} whatsapp contact", self.phone_pattern)
        valid_numbers = []
        for number in found_numbers:
            try:
                parsed_number = phonenumbers.parse(number)
                if phonenumbers.is_valid_number(parsed_number):
                    formatted_number = phonenumbers.format_number(
                        parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL
                    )
                    valid_numbers.append(formatted_number)
            except:
                continue
        return valid_numbers

# Streamlit App
st.title("Username OSINT Tool")
st.markdown("This tool helps you gather OSINT information about a username across multiple platforms.")

username = st.text_input("Enter a username to search:")

if st.button("Run OSINT"):
    if username:
        osint = UsernameOSINT(username)
        
        st.subheader("Social Media Profiles")
        platforms = {
            "GitHub": lambda: osint.check_github(),
            "Instagram": lambda: osint.check_platform(f"https://www.instagram.com/{username}/"),
            "Twitter": lambda: osint.check_platform(f"https://twitter.com/{username}"),
            "LinkedIn": lambda: osint.check_platform(f"https://www.linkedin.com/in/{username}/"),
            "Medium": lambda: osint.check_platform(f"https://medium.com/@{username}")
        }
        
        for platform, check_function in platforms.items():
            with st.spinner(f"Checking {platform}..."):
                result = check_function()
                if platform == "GitHub" and result["exists"]:
                    st.success(f"{platform} profile found!")
                    for key, value in result.items():
                        if key != "exists" and value:
                            st.write(f"- {key}: {value}")
                elif result["exists"]:
                    st.success(f"{platform} profile found!")
                else:
                    st.error(f"No {platform} profile found.")

        st.subheader("Searching for Emails")
        with st.spinner("Searching for emails..."):
            emails = osint.search_emails()
        if emails:
            st.success(f"Found {len(emails)} email(s):")
            for email in emails:
                st.write(f"- {email}")
        else:
            st.error("No email addresses found.")

        st.subheader("Searching for WhatsApp Numbers")
        with st.spinner("Searching for WhatsApp numbers..."):
            whatsapp_numbers = osint.search_whatsapp()
        if whatsapp_numbers:
            st.success(f"Found {len(whatsapp_numbers)} number(s):")
            for number in whatsapp_numbers:
                st.write(f"- {number}")
        else:
            st.error("No WhatsApp numbers found.")
    else:
        st.error("Please enter a username to proceed.")
