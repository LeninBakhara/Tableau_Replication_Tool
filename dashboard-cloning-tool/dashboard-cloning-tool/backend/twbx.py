import zipfile
import os
import shutil
import re
from datetime import datetime

def patch_twbx(template_path: str, client_name: str, datasource_mappings: list, output_dir: str) -> dict:
    """
    Patch a .twbx file by replacing dummy column names with real column names.

    datasource_mappings: list of dicts:
      {
        "datasource_caption": "BlueBottle_Marketing_Ads",
        "old_table": "marketing_ads",
        "new_table": "tulip_marketing_ads",   # new client table
        "old_schema": "dbt_bluebottle_prod",
        "new_schema": "dc_j450",              # new client schema
        "column_mapping": {
          "accountid": "account_id_new",      # old_col -> new_col
          ...
        }
      }
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_client = re.sub(r'[^a-zA-Z0-9_]', '_', client_name)
    output_filename = f"{safe_client}_{timestamp}.twbx"
    output_path = os.path.join(output_dir, output_filename)

    # Read the .twb from the zip
    with zipfile.ZipFile(template_path, 'r') as zin:
        filelist = zin.namelist()
        twb_name = next((f for f in filelist if f.endswith('.twb')), None)
        if not twb_name:
            return {"success": False, "error": "No .twb file found in template"}

        twb_content = zin.read(twb_name).decode('utf-8', errors='replace')

        # Write everything except the .twb to new zip first
        with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
            for item in filelist:
                if item == twb_name:
                    continue
                zout.writestr(item, zin.read(item))

    # Apply all datasource mappings
    patched = twb_content
    for ds_map in datasource_mappings:
        old_table = ds_map.get("old_table", "")
        new_table = ds_map.get("new_table", "")
        old_schema = ds_map.get("old_schema", "")
        new_schema = ds_map.get("new_schema", "")
        col_mapping = ds_map.get("column_mapping", {})

        # Replace schema
        if old_schema and new_schema and old_schema != new_schema:
            patched = patched.replace(f'schema="{old_schema}"', f'schema="{new_schema}"')
            patched = patched.replace(f"[{old_schema}]", f"[{new_schema}]")

        # Replace table name
        if old_table and new_table and old_table != new_table:
            patched = patched.replace(f'[{old_schema}].[{old_table}]', f'[{new_schema}].[{new_table}]')
            patched = patched.replace(f'table="[{old_schema}].[{old_table}]"', f'table="[{new_schema}].[{new_table}]"')
            patched = patched.replace(f'name="{old_table}"', f'name="{new_table}"')

        # Replace column names (wrapped in brackets as Tableau uses [col_name])
        for old_col, new_col in col_mapping.items():
            if old_col and new_col and old_col != new_col:
                # Replace [old_col] with [new_col] - careful not to replace partial matches
                patched = patched.replace(f'[{old_col}]', f'[{new_col}]')
                # Also replace in name= attributes
                patched = patched.replace(f'name="[{old_col}]"', f'name="[{new_col}]"')

    # Write the patched .twb back
    with zipfile.ZipFile(output_path, 'a', compression=zipfile.ZIP_DEFLATED) as zout:
        zout.writestr(twb_name, patched.encode('utf-8'))

    return {
        "success": True,
        "output_file": output_filename,
        "output_path": output_path
    }


def extract_datasource_info(template_path: str) -> list:
    """Extract datasource info from a .twbx template"""
    import xml.etree.ElementTree as ET

    with zipfile.ZipFile(template_path, 'r') as z:
        twb_name = next((f for f in z.namelist() if f.endswith('.twb')), None)
        if not twb_name:
            return []
        content = z.read(twb_name)

    root = ET.fromstring(content)
    seen = set()
    datasources = []

    for ds in root.findall('.//datasource'):
        caption = ds.get('caption', '')
        if not caption or caption in seen:
            continue
        seen.add(caption)

        tables = []
        schemas = []
        for rel in ds.findall('.//relation'):
            t = rel.get('table', '')
            if t and '[' in t:
                # Format: [schema].[table]
                parts = t.strip('[]').split('].[')
                if len(parts) == 2:
                    schemas.append(parts[0])
                    tables.append(parts[1])

        cols = []
        for col in ds.findall('.//column'):
            name = col.get('name', '')
            if name and not name.startswith('[__') and name != '[:Measure Names]' and '(copy)' not in name and 'Calculation' not in name:
                clean = name.strip('[]')
                cols.append({
                    "name": clean,
                    "datatype": col.get('datatype', 'string'),
                    "role": col.get('role', 'dimension')
                })

        if cols:
            datasources.append({
                "caption": caption,
                "table": tables[0] if tables else "",
                "schema": schemas[0] if schemas else "",
                "columns": cols
            })

    return datasources
