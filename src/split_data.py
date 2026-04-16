##
# @file       split_data.py
# @author     Andrias Zelele
# @date       2025-04-15
# @brief      Splits a math contest results CSV file into two normalized CSV
#             files (Institutions and Teams) ready for SQL database import.
#
# @description
#   This program reads a contest CSV file provided as a command-line argument,
#   deduplicates institutions by (name, city, state/province, country), assigns
#   each a unique integer ID, and writes two output files:
#     - Institutions_YYYY.csv  : one row per unique institution
#     - Teams_YYYY.csv         : one row per team, linked by Institution ID
#
#   The output filenames are derived automatically from the input filename.
#   For example, passing 'doc/2015.csv' produces 'Institutions_2015.csv'
#   and 'Teams_2015.csv'.
#
# @usage      python src/split_data.py doc/2015.csv
# @version    1.0
##

import argparse
import csv
import os
import sys

##
# @brief Set of column names that must be present in the input CSV file.
#        The program will exit with an error if any of these are missing.
##
REQUIRED_COLUMNS = {
    "Institution",
    "Team Number",
    "City",
    "State/Province",
    "Country",
    "Advisor",
    "Problem",
    "Ranking"
}


def parse_args() -> str:
    """
    @brief  Resolves the input file path either from the command-line argument
            or by prompting the user if none was provided.

    @details
        If the user runs the script with a filename argument, that path is used.
        If no argument is given, the user is prompted to enter a filename
        interactively. The prompt repeats until a non-empty value is entered.

    @return The input file path as a string.
    """
    parser = argparse.ArgumentParser(
        description="Split a math contest CSV into Institutions.csv and Teams.csv."
    )

    # Optional positional argument: if omitted, the user will be prompted
    parser.add_argument(
        "input_file",
        nargs="?",
        default=None,
        help="Path to the input CSV file (e.g. doc/2015.csv, doc/2016.csv)"
    )

    args = parser.parse_args()

    # If no filename was provided on the command line, prompt the user
    if args.input_file is None:
        print("No file provided.")
        while True:
            input_path = input("Please enter the path to your CSV file: ").strip()
            if input_path:
                return input_path
            print("ERROR: File path cannot be empty. Please try again.")

    return args.input_file


def derive_output_paths(input_path: str) -> tuple[str, str]:
    """
    @brief  Derives output CSV filenames from the input filename.

    @details
        Strips the directory and extension from the input path and uses the
        base name to construct the two output filenames. For example:
            'doc/2016.csv' -> ('Institutions_2016.csv', 'Teams_2016.csv')

    @param  input_path  Path to the input CSV file.
    @return A tuple of (institutions_path, teams_path) as strings.
    """
    # os.path.basename strips the directory  -> '2015.csv'
    # os.path.splitext strips the extension  -> ('2015', '.csv')
    base = os.path.splitext(os.path.basename(input_path))[0]

    return f"Institutions_{base}.csv", f"Teams_{base}.csv"


def validate_file_exists(input_path: str) -> None:
    """
    @brief  Validates that the input file exists on disk and is not empty.

    @details
        This check runs before attempting to open or parse the file, so the
        user receives a clear error message rather than a Python traceback.
        Exits the program with a descriptive error message if either check fails.

    @param  input_path  Path to the input CSV file.
    @return None
    """
    # Check that the file exists at the given path
    if not os.path.exists(input_path):
        sys.exit(
            f"ERROR: '{input_path}' not found.\n"
            f"Make sure the file is in the correct directory: {os.getcwd()}"
        )

    # Check that the file is not completely empty (0 bytes)
    if os.path.getsize(input_path) == 0:
        sys.exit(f"ERROR: '{input_path}' is empty.")


def open_csv(input_path: str) -> list[dict]:
    """
    @brief  Opens and reads a CSV file into a list of row dictionaries,
            handling multiple encodings robustly.

    @details
        Attempts to decode the file using utf-8-sig, utf-8, and latin-1
        in that order. utf-8-sig automatically strips a standard UTF-8 BOM.
        If a BOM was double-encoded (common in Excel exports), the first
        column key is cleaned manually by re-encoding and stripping the BOM
        character. Exits the program if no encoding succeeds.

    @param  input_path  Path to the input CSV file.
    @return A list of dicts where each dict represents one row,
            with column names as keys and cell values as values.
    """
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            with open(input_path, encoding=encoding, newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            # If the BOM was not fully stripped, it remains on the first column
            # name. Re-encode as latin-1 and decode as utf-8 to reveal and
            # remove the BOM character (\ufeff).
            if rows:
                first_key = next(iter(rows[0]))
                clean_key = first_key.encode("latin-1").decode("utf-8").lstrip("\ufeff")

                # Rename the mangled key across all rows if it differs
                if first_key != clean_key:
                    for row in rows:
                        row[clean_key] = row.pop(first_key)

            return rows

        except (UnicodeDecodeError, UnicodeError):
            # This encoding did not work — try the next one
            continue

    sys.exit(f"ERROR: Could not decode '{input_path}'. Try saving it as UTF-8.")


def validate_contents(input_path: str, rows: list[dict]) -> None:
    """
    @brief  Validates that the parsed CSV contains the required columns
            and at least one data row.

    @details
        Uses set subtraction to identify any missing columns and reports
        them all at once, so the user can fix everything in one pass.
        Exits the program with a descriptive error message if validation fails.

    @param  input_path  Path to the input CSV file (used in error messages).
    @param  rows        List of row dicts returned by open_csv().
    @return None
    """
    # A file with a header but no data rows is not useful
    if not rows:
        sys.exit(f"ERROR: '{input_path}' has a header but no data rows.")

    # Extract the column names present in the file
    columns = set(rows[0].keys())

    # Set subtraction: anything in REQUIRED_COLUMNS but not in columns is missing
    missing = REQUIRED_COLUMNS - columns
    if missing:
        sys.exit(
            f"ERROR: '{input_path}' is missing expected column(s): {', '.join(sorted(missing))}\n"
            f"Found columns: {', '.join(sorted(columns))}"
        )

    print(f"OK: '{input_path}' passed all validation checks.")


def build_institution_map(rows: list[dict]) -> dict[tuple, int]:
    """
    @brief  Builds a deduplicated mapping of institutions to unique integer IDs.

    @details
        Each institution is identified by a 4-tuple key:
            (Institution Name, City, State/Province, Country)
        This handles cases where two institutions share the same name but are
        located in different cities or countries. IDs are assigned in the order
        institutions are first encountered, starting from 1.

    @param  rows  List of row dicts returned by open_csv().
    @return A dict mapping each (name, city, state, country) tuple to a unique int ID.
    """
    inst_map = {}  # Maps institution key tuple -> unique integer ID
    next_id = 1    # Auto-incrementing ID counter

    for row in rows:
        # Build the deduplication key from the four identifying fields
        key = (row["Institution"], row["City"], row["State/Province"], row["Country"])

        # Only assign a new ID if this institution has not been seen before
        if key not in inst_map:
            inst_map[key] = next_id
            next_id += 1

    print(f"Found {len(inst_map)} unique institution(s) across {len(rows)} team(s).")
    return inst_map


def write_institutions(inst_map: dict[tuple, int], output_path: str) -> None:
    """
    @brief  Writes the deduplicated institution data to a CSV file.

    @details
        Iterates over the institution map and writes one row per unique
        institution, including its auto-generated ID. Catches PermissionError
        in case the output file is already open in another program (e.g. Excel).

    @param  inst_map     Dict mapping (name, city, state, country) tuples to IDs.
    @param  output_path  Path where the institutions CSV will be written.
    @return None
    """
    try:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Write the header row
            writer.writerow(["Institution ID", "Institution Name", "City", "State/Province", "Country"])

            # Write one row per unique institution
            for (name, city, state, country), iid in inst_map.items():
                writer.writerow([iid, name, city, state, country])

        print(f"Wrote {len(inst_map)} institution(s) to '{output_path}'.")

    except PermissionError:
        sys.exit(
            f"ERROR: Permission denied when writing '{output_path}'. "
            f"Is the file open in another program?"
        )


def write_teams(rows: list[dict], inst_map: dict[tuple, int], output_path: str) -> None:
    """
    @brief  Writes team data to a CSV file, linking each team to its institution
            via a foreign key.

    @details
        For each team row, reconstructs the institution key and looks up the
        corresponding ID from inst_map. This ID is written as the Institution ID
        column, forming the relational link between the two output files.
        Catches PermissionError in case the output file is open in another program.

    @param  rows         List of row dicts returned by open_csv().
    @param  inst_map     Dict mapping (name, city, state, country) tuples to IDs.
    @param  output_path  Path where the teams CSV will be written.
    @return None
    """
    try:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Write the header row
            writer.writerow(["Team Number", "Advisor", "Problem", "Ranking", "Institution ID"])

            # Write one row per team, including the institution foreign key
            for row in rows:
                # Rebuild the key to look up this team's institution ID
                key = (row["Institution"], row["City"], row["State/Province"], row["Country"])
                iid = inst_map[key]

                writer.writerow([
                    row["Team Number"],
                    row["Advisor"],
                    row["Problem"],
                    row["Ranking"],
                    iid
                ])

        print(f"Wrote {len(rows)} team(s) to '{output_path}'.")

    except PermissionError:
        sys.exit(
            f"ERROR: Permission denied when writing '{output_path}'. "
            f"Is the file open in another program?"
        )


def main():
    """
    @brief  Entry point of the program. Orchestrates argument parsing,
            validation, data processing, and file output.

    @details
        Calls each function in the correct order:
            1. Parse the command-line argument to get the input file path.
            2. Derive output filenames from the input filename.
            3. Validate the file exists and is not empty.
            4. Open and parse the CSV file.
            5. Validate the parsed contents.
            6. Build the institution deduplication map.
            7. Write the institutions output file.
            8. Write the teams output file.

    @return None
    """
    # Step 1: Resolve the input file path from argument or user prompt
    input_path = parse_args()

    # Step 2: Derive output filenames from the input filename
    institutions_path, teams_path = derive_output_paths(input_path)

    # Step 3: Validate the file exists and is not empty
    validate_file_exists(input_path)

    # Step 4: Open and parse the CSV file
    rows = open_csv(input_path)

    # Step 5: Validate the parsed contents
    validate_contents(input_path, rows)

    # Step 6: Build the institution deduplication map
    inst_map = build_institution_map(rows)

    # Step 7: Write the institutions output file
    write_institutions(inst_map, institutions_path)

    # Step 8: Write the teams output file
    write_teams(rows, inst_map, teams_path)

    print(f"\nDone! Output files are ready: {institutions_path}, {teams_path}")


##
# @brief  Standard Python entry point guard.
#         Ensures main() is only called when this script is run directly,
#         not when it is imported as a module by another script.
##
if __name__ == "__main__":
    main()