# PDF-Hunter-
Baseline PDF hunter for scouring your site to flag for ADA complaince.
#!/usr/bin/env python3
"""
README:
-------
Tool: Local WordPress PDF Link Scanner
Purpose: Scans a local WordPress (not limited to) site's sitemap recursively to find pages referencing PDF files.
         It excludes raw upload paths (/wp-content/) and sitemap files, focusing on content pages.
         Designed for local environments with self-signed SSL certificates.

PDF_hunter_live.py should not be used as is, read the comment at start of file before use.

Dependencies:
-------------
1. Python 3.x
2. requests
3. beautifulsoup4
4. urllib3 

Usage:
------
1. Ensure your local WordPress site is running and accessible.
2. Update BASE_URL below to match your local domain (e.g., https://websitehere.local).
3. Run: pdf_hunter.py
4. Output is saved to 'pages_with_pdfs.txt' in the current directory.

Configuration:
--------------
- Excludes: /wp-content/, sitemaps
- Includes: /event/, /post/, /page/ (and other content types)
- SSL: Disabled (verify=False) for self-signed certs.
"""
