# workflow-fixes/run_populate_data1.py
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import sys

from populate_data1_angular import get_records as get_part1
from make_data_part2 import get_part2_records as get_part2
from make_data_part3 import get_part3_records as get_part3
from make_data_part4 import get_part4_records as get_part4

NEW_HEADERS = [
    "Name of Tool/Infra",
    "Category",
    "Version",
    "Purpose",
    "Record Type (Upstream Original Tool / Recommended Fork Alternate)",
    "Alternate of which too/infra (Mapping to Upstream Original Tool /infra)",
    "Reason of selecting this tool",
    "Any usage Limit",
    "Free/Paid",
    "Access-restricted, blocked, not publicly accessible, or unavailable for purchase",
    "License",
    "SPDX License Identifier (e.g., MIT, Apache-2.0, Commercial SaaS EULA)",
    "Copyleft / Viral Source Disclosure Risk (None / Permissive vs Weak Copyleft vs Strong Copyleft)",
    "Commercial Redistribution Rights (Permitted / Restricted / Non-commercial only)",
    "Telemetry & Code Exfiltration Risk (Local-only / Cloud SaaS logs / High)",
    "Attribution / Notice Requirements (Standard notice / None)",
    "Permissible for Company Fork Release? (Legal Verdict)",
    "Subscription Models Vailable",
    "Selected Subscription Model",
    "Reason of selecting this subscription model",
    "Functional Category",
    "Conponent Name",
    "workflow name",
    "workflow yml",
    "User Limit",
    "User / Concurrency / Usage Limits",
    "Token/Key/Secret Based access",
    "Lincese Suitable for 5 member team and reason",
    "Subscription Suitable for 5 member team and reason",
    "Required to Purchase ?",
    "Why Upstream Uses It",
    "Access Status in Fork",
    "Is It Mandatory in Fork? (Yes / No - Can be discarded)",
    "Suitable for Release from Fork? (Yes/No + Reason)",
    "Official site",
    "Purchase Link",
    "Price Link",
    "Is it suitable for release from Forked Opensource Model ? Reason",
    "why it not suitable for release from Forked Opensource Model",
    "Alternate Options for release from Forked Opensource Model",
    "Best One alternate Option for release from Forked Opensource Model (with name and version)",
    "Reson of seleting that Best One alternate Option for release from Forked Opensource Model",
    "Replaces Upstream Tool (Name of original tool if this is an alternate)",
    "issues identified in master_list",
    "List of all evidence  verified"
]

def main():
    excel_path = 'workflow-fixes/data1.xlsx'
    print(f"Loading {excel_path}...")
    wb = openpyxl.load_workbook(excel_path)
    ws = wb['angular']

    headers = NEW_HEADERS
    print(f"Using {len(headers)} standardized columns.")

    # Combine all parts
    all_records = []
    all_records.extend(get_part1())
    all_records.extend(get_part2())
    all_records.extend(get_part3())
    all_records.extend(get_part4())

    print(f"Total compiled records to insert: {len(all_records)}")

    # Clear existing data rows (if any)
    if ws.max_row > 1:
        ws.delete_rows(2, ws.max_row - 1)

    # Styles
    font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    fill_header = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid") # Dark Navy Blue
    
    font_upstream = Font(name="Calibri", size=10, bold=False, color="000000")
    fill_upstream = PatternFill(start_color="F2F4F7", end_color="F2F4F7", fill_type="solid") # Soft Cool Gray

    font_alternate = Font(name="Calibri", size=10, bold=False, color="000000")
    fill_alternate = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid") # Soft Light Green

    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )

    align_center = Alignment(horizontal="center", vertical="top", wrap_text=True)
    align_left = Alignment(horizontal="left", vertical="top", wrap_text=True)

    # Style Header Row on sheet 'angular'
    ws.row_dimensions[1].height = 36
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border

    # Insert Data Rows on sheet 'angular'
    current_row = 2
    for rec in all_records:
        rec_type = rec.get("Record Type (Upstream Original Tool / Recommended Fork Alternate)", "")
        is_alternate = "Recommended Fork Alternate" in rec_type

        row_fill = fill_alternate if is_alternate else fill_upstream
        row_font = font_alternate if is_alternate else font_upstream

        ws.row_dimensions[current_row].height = 45 # comfortable reading height

        for col_idx, header in enumerate(headers, start=1):
            cell = ws.cell(row=current_row, column=col_idx)
            val = rec.get(header, "")
            cell.value = val
            cell.font = row_font
            cell.fill = row_fill
            cell.border = thin_border

            # Center align short categorical fields
            if header in ["Category", "Version", "Free/Paid", "workflow yml", "Required to Purchase ?", 
                          "Access Status in Fork", "Is It Mandatory in Fork? (Yes / No - Can be discarded)", 
                          "Record Type (Upstream Original Tool / Recommended Fork Alternate)",
                          "Permissible for Company Fork Release? (Legal Verdict)"]:
                cell.alignment = align_center
            else:
                cell.alignment = align_left

        current_row += 1

    # Auto-adjust column widths on 'angular'
    print("Adjusting column widths for sheet 'angular'...")
    for col_idx in range(1, len(headers) + 1):
        col_letter = get_column_letter(col_idx)
        header_text = str(headers[col_idx - 1] or "")
        max_len = len(header_text)
        
        # sample rows
        for r in range(2, min(ws.max_row + 1, 20)):
            val_text = str(ws.cell(r, col_idx).value or "")
            if len(val_text) > max_len and len(val_text) < 60:
                max_len = len(val_text)

        adjusted_width = max(max_len + 3, 14)
        if adjusted_width > 55:
            adjusted_width = 55 # cap width for ultra-long description columns
        ws.column_dimensions[col_letter].width = adjusted_width

    # Propagate 45-column headers to other component sheets
    other_sheets = ['template', 'nodejs', 'spring_boot', 'graal', 'k3s']
    for sname in other_sheets:
        if sname in wb.sheetnames:
            ows = wb[sname]
            ows.row_dimensions[1].height = 36
            for col_idx, header in enumerate(headers, start=1):
                c = ows.cell(row=1, column=col_idx, value=header)
                c.font = font_header
                c.fill = fill_header
                c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                c.border = thin_border
            # Adjust widths for row 1
            for col_idx in range(1, len(headers) + 1):
                col_letter = get_column_letter(col_idx)
                header_text = str(headers[col_idx - 1] or "")
                ows.column_dimensions[col_letter].width = max(len(header_text) + 3, 14)
            print(f"Propagated {len(headers)} headers to sheet '{sname}'.")

    print(f"Saving workbook with {current_row - 2} data rows...")
    wb.save(excel_path)
    print("Successfully saved workflow-fixes/data1.xlsx!")

if __name__ == '__main__':
    main()
