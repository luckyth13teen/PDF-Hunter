#!/usr/bin/env python3
"""
README:

THIS IS A BAD BOT AND SHOULD NOT BE USED AS IS
This bot breaks the majority of rules for how a bot should operate ethically
This tool is only for site owners unable to copy down a local version of their site to do the primary script
DO NOT USE THIS WITHOUT PERMISSION OF SITE OWNERS/WHITELISTING IP OF SOURCE/ETC

-------
Tool: Remote WordPress PDF Link Scanner (Stealth Mode)
Purpose: Recursively scans a live WordPress site's sitemap to find pages referencing PDF files.
         Designed to minimize server load and avoid triggering WAF/Rate Limits.
         Excludes raw upload paths (/wp-content/) and sitemap files.

Dependencies:
-------------
1. Python 3.x
2. requests
3. beautifulsoup4
4. urllib3

Installation:
-------------
pip install requests beautifulsoup4 urllib3

Usage:
------
1. Update BASE_URL to the live site domain (e.g., https://example.com).
2. Run: python pdf_scanner_remote.py
3. Output is saved to 'pages_with_pdfs.txt' in the current directory.

Safety Features:
----------------
- Random delays (5-15s) between requests.
- Auto-retry on 429/202 errors.
- Immediate stop on 403 Forbidden.
- Browser User-Agent spoofing.
"""

import requests
import xml.etree.ElementTree as ET
import urllib3
import time
import random
import sys

# Suppress SSL warnings (only if using self-signed certs remotely, otherwise safe to ignore)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================= CONFIGURATION =================
BASE_URL = "https://www.carolinehd.org"  # UPDATE THIS to your live site
START_SITEMAP = f"{BASE_URL}/sitemap_index.xml"
OUTPUT_FILE = "pages_with_pdfs.txt"
TIMEOUT = 30
VERBOSE = True
# =================================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive"
}

session = requests.Session()
session.headers.update(HEADERS)

def fetch_text(url):
    try:
        # Random delay to mimic human behavior (5-10s)
        delay = random.uniform(5.0, 10.0)
        if VERBOSE:
            print(f"  [Waiting {delay:.1f}s before fetching {url}]")
        time.sleep(delay)

        resp = session.get(url, timeout=TIMEOUT)
        
        # Handle blocking/rate limiting
        if resp.status_code == 403:
            print(f"[!] 403 Forbidden: IP likely blocked. STOPPING.")
            sys.exit(1)
        if resp.status_code == 429:
            print(f"[!] 429 Too Many Requests. Waiting 60s before retry...")
            time.sleep(60)
            return fetch_text(url)
        if resp.status_code == 202:
            print(f"[!] 202 Accepted. Waiting 10s before retry...")
            time.sleep(10)
            return fetch_text(url)
        if resp.status_code != 200:
            print(f"[!] HTTP Error {resp.status_code} for {url}")
            return None
            
        return resp.text
    except Exception as e:
        if "202" in str(e) or "Connection" in str(e):
            print(f"[!] Connection issue. Waiting 15s and retrying...")
            time.sleep(15)
            return fetch_text(url)
        if VERBOSE:
            print(f"[!] Failed to fetch {url}: {e}")
        return None

def normalize_url(url):
    if url.startswith('//'):
        return "https:" + url
    return url

def is_excluded(url):
    if "/wp-content/" in url:
        return True
    if "sitemap" in url:
        return True
    return False

def get_all_urls_from_sitemap(sitemap_url, collected_urls=None):
    if collected_urls is None:
        collected_urls = set()

    xml_content = fetch_text(sitemap_url)
    if not xml_content:
        return collected_urls

    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        if VERBOSE:
            print(f"[!] XML Parse Error for {sitemap_url}: {e}")
        return collected_urls

    NS = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

    # Check for Sitemap Index
    sitemaps = root.findall('ns:sitemap', NS)
    if not sitemaps:
        sitemaps = root.findall('sitemap')

    if sitemaps:
        if VERBOSE:
            print(f"[*] Detected Sitemap Index. Found {len(sitemaps)} child sitemaps.")
        
        for sm in sitemaps:
            loc_elem = sm.find('ns:loc', NS)
            if loc_elem is None:
                loc_elem = sm.find('loc')
            
            if loc_elem is not None:
                child_url = normalize_url(loc_elem.text.strip())
                if child_url not in collected_urls:
                    get_all_urls_from_sitemap(child_url, collected_urls)
        return collected_urls

    # Check for Standard Sitemap URLs
    urls = root.findall('ns:url', NS)
    if not urls:
        urls = root.findall('url')

    count = 0
    excluded_count = 0
    
    for url_elem in urls:
        loc_elem = url_elem.find('ns:loc', NS)
        if loc_elem is None:
            loc_elem = url_elem.find('loc')
        
        if loc_elem is not None:
            url = normalize_url(loc_elem.text.strip())
            
            if is_excluded(url):
                excluded_count += 1
                continue
            
            collected_urls.add(url)
            count += 1
            
            if count <= 5 and VERBOSE:
                print(f"  [INCLUDED] {url}")
    
    if VERBOSE:
        msg = f"[+] Extracted {count} valid pages from {sitemap_url}"
        if excluded_count > 0:
            msg += f" (excluded {excluded_count})"
        print(msg)
        
    return collected_urls

def scan_page_for_pdfs(url):
    try:
        # Random delay between page scans (8-15s)
        delay = random.uniform(8.0, 15.0)
        if VERBOSE:
            print(f"  [Waiting {delay:.1f}s before scanning {url}]")
        time.sleep(delay)

        resp = session.get(url, timeout=TIMEOUT)
        
        if resp.status_code == 403:
            print(f"[!] Blocked at {url}. STOPPING.")
            sys.exit(1)
        if resp.status_code != 200:
            return False
        
        if url.lower().endswith('.pdf'):
            return True
        
        if '.pdf' in resp.text.lower():
            return True
            
        return False
    except Exception as e:
        if "202" in str(e) or "Connection" in str(e):
            print(f"[!] Connection issue at {url}. Waiting 20s and retrying...")
            time.sleep(20)
            return scan_page_for_pdfs(url)
        if VERBOSE:
            print(f"[!] Error scanning {url}: {e}")
        return False

def main():
    print(f"[*] REMOTE SCAN MODE: {BASE_URL}")
    print(f"[*] Entry point: {START_SITEMAP}")
    print(f"[*] Exclusions: /wp-content/, sitemaps (Events INCLUDED)")
    print(f"[*] Safety: Random delays, Auto-retry on 429/202, Stop on 403\n")
    
    all_urls = get_all_urls_from_sitemap(START_SITEMAP)
    
    if not all_urls:
        print("\n[!] ERROR: No valid pages found.")
        return

    if VERBOSE:
        print(f"\n[*] Total unique pages to scan: {len(all_urls)}\n")

    pages_with_pdfs = []
    
    for i, page_url in enumerate(all_urls):
        has_pdf = scan_page_for_pdfs(page_url)
        
        if VERBOSE:
            status = "YES" if has_pdf else "NO"
            print(f"({i+1}/{len(all_urls)}) [{status}] {page_url}")
        
        if has_pdf:
            pages_with_pdfs.append(page_url)

    if pages_with_pdfs:
        with open(OUTPUT_FILE, 'w') as f:
            for page in sorted(pages_with_pdfs):
                f.write(page + '\n')
        print(f"\n[+] Done! Found {len(pages_with_pdfs)} pages referencing PDFs.")
        print(f"[+] Saved to {OUTPUT_FILE}")
    else:
        print("\n[-] No pages with PDF references found.")

if __name__ == "__main__":
    main()