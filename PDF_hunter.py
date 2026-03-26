
import requests
import xml.etree.ElementTree as ET
import urllib3
import sys

# Suppress SSL warnings for local self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================= CONFIGURATION =================
BASE_URL = "https://websitehere.local"  
START_SITEMAP = f"{BASE_URL}/sitemap_index.xml"
OUTPUT_FILE = "pages_with_pdfs.txt"
TIMEOUT = 30
VERBOSE = True
# =================================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

session = requests.Session()
session.headers.update(HEADERS)

def fetch_text(url):
    try:
        resp = session.get(url, timeout=TIMEOUT, verify=False)
        if resp.status_code != 200:
            return None
        return resp.text
    except Exception as e:
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
        resp = session.get(url, timeout=TIMEOUT, verify=False)
        if resp.status_code != 200:
            return False
        
        if url.lower().endswith('.pdf'):
            return True
        
        if '.pdf' in resp.text.lower():
            return True
            
        return False
    except Exception as e:
        if VERBOSE:
            print(f"[!] Error scanning {url}: {e}")
        return False

def main():
    print(f"[*] LOCAL SCAN MODE: {BASE_URL}")
    print(f"[*] Entry point: {START_SITEMAP}")
    print(f"[*] Exclusions: /wp-content/, sitemaps (Events INCLUDED)")
    print(f"[*] SSL: Verification DISABLED\n")
    
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