# -*- coding: utf-8 -*-
import requests
import sys
import os
import pandas as pd
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

# --- ======================================================= ---
# --- CONFIGURATION - ACTION REQUIRED
# --- ======================================================= ---
# PASTE YOUR ZENROWS API KEY HERE
ZENROWS_API_KEY ='078059fabdecaeda7f87fff975992e926e8220cb' 

# --- ======================================================= ---
# --- ROBUST PATHING LOGIC
# --- ======================================================= ---
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
INPUT_DIR = os.path.join(PROJECT_ROOT, 'entrada')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'salida')

# --- FILE AND FOLDER CONFIGURATION ---
# *** CHANGE 1: Updated the input file name to reflect the new list.
INPUT_FILE_NAME = 'Book3.xlsx' 
OUTPUT_FILE_NAME = 'generated_output_book3.xlsx'

# *** CHANGE 2 & 3: Updated column names to match the new Excel file from the image.
INPUT_COLUMN_SKU = 'Code'
INPUT_COLUMN_DESC = 'Description (English)'

# --- ======================================================= ---
# --- SEARCH ENGINE (Unchanged ZenRows Function)
# --- ======================================================= ---

def run_google_search(search_query):
    """Runs a single Google search and returns the parsed leads."""
    print(f"    -> Executing search for: '{search_query[:70]}...'")
    target_url = f"https://www.google.com/search?q={quote_plus(search_query)}"
    
    params = {
        'url': target_url,
        'apikey': ZENROWS_API_KEY,
        'js_render': 'true',
        'premium_proxy': 'true',
        'antibot': 'true',
        'wait_for': 'div#search'
    }
    
    try:
        response = requests.get('https://api.zenrows.com/v1/', params=params, timeout=240)
        
        if response.status_code != 200:
            print(f"    -> FAILED: ZenRows responded with status code {response.status_code}.")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        search_results = soup.select('div.yuRUbf a')
        
        leads = []
        for link_element in search_results:
            title_element = link_element.select_one('h3')
            if title_element:
                url = link_element.get('href')
                title = title_element.text
                if url and url.startswith('http'):
                    leads.append({'title': title, 'url': url})
        print(f"    -> SUCCESS: Found {len(leads)} results.")
        return leads

    except Exception as e:
        print(f"    -> UNEXPECTED ERROR during search: {e}")
        return []

# --- ======================================================= ---
# --- MAIN SCRIPT (Mission Controller)
# --- ======================================================= ---

def main():
    """Main function that orchestrates the entire process."""
    print("--- STARTING BATCH DISCOVERY MISSION (v2.2 - New Biotex List) ---")

    # 1. Critical API Key Check
    if not ZENROWS_API_KEY or len(ZENROWS_API_KEY) < 10:
        print("\n[CRITICAL ERROR] ZENROWS_API_KEY is not set in the script.")
        print("Please edit the file and add your API key to continue.")
        sys.exit(1)

    # 2. Define full file paths
    input_file_path = os.path.join(INPUT_DIR, INPUT_FILE_NAME)
    output_file_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE_NAME)
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 3. Read the input Excel file
    try:
        print(f"\nReading input file: {input_file_path}")
        df_input = pd.read_excel(input_file_path)
        print(f"File read successfully. Found {len(df_input)} products to process.")
    except FileNotFoundError:
        print(f"\n[CRITICAL ERROR] Input file not found: '{input_file_path}'")
        print("Please double-check the file name and its location.")
        sys.exit(1)

    # 4. Process each product from the Excel file
    all_results_data = []

    for index, row in df_input.iterrows():
        # Using .get() with a default value makes it safer if a column is missing
        sku = str(row.get(INPUT_COLUMN_SKU, ''))
        description = str(row.get(INPUT_COLUMN_DESC, ''))

        # Skip rows where the code/sku is empty
        if not sku:
            print(f"\n--- Skipping Row #{index + 1}: SKU is empty. ---")
            continue

        print(f"\n--- Processing Row #{index + 1}: SKU = {sku} ---")

        sku_query = f'"{sku}"'
        description_query = f"{sku} {description}"
        
        print("  [Stage 1/2] Searching by exact Code...")
        stage1_leads = run_google_search(sku_query)
        
        print("  [Stage 2/2] Searching by Code + Description...")
        stage2_leads = run_google_search(description_query)

        total_leads = stage1_leads + stage2_leads
        unique_leads = {lead['url']: lead for lead in total_leads}.values()
        
        if not unique_leads:
            print(f"  -> Mission for '{sku}' complete. No leads found.")
            all_results_data.append({
                'Original Code': sku,
                'Original Description': description,
                'Found Title': 'No suppliers found',
                'URL': ''
            })
        else:
            print(f"  -> Mission for '{sku}' complete. Found {len(unique_leads)} unique leads.")
            for lead in unique_leads:
                all_results_data.append({
                    'Original Code': sku,
                    'Original Description': description,
                    'Found Title': lead['title'],
                    'URL': lead['url']
                })
    # 5. Generate the final Excel report
    print("\n--- PROCESS COMPLETE. Generating final report... ---")
    
    if all_results_data:
        # Fíjate que todo lo que está debajo de este 'if' lleva 4 espacios
        try:
            # Y todo lo que está dentro del 'try' lleva 8 espacios
            print(f"  -> Attempting to save report to: {output_file_path}")
            results_df = pd.DataFrame(all_results_data)
            results_df.to_excel(output_file_path, index=False, engine='openpyxl')
            print(f"\n[SUCCESS] Report has been saved to: {output_file_path}")
        
        except Exception as e:
            # El 'except' está al mismo nivel que el 'try' (4 espacios)
            print(f"\n[CRITICAL ERROR DURING SAVE] Failed to save the Excel file.")
            print(f"  -> The specific error is: {e}")
            
    else:
        # El 'else' está al mismo nivel que el 'if' (sin espacios extras)
        print("\nNo results were generated to save.")

if __name__ == "__main__":
    main()
