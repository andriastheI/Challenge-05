# Challenge-05 – Contest CSV Splitter

A console-based Python application that splits a math contest results CSV file
into two separate, linked CSV files — one for institutions and one for teams —
ready for import into a SQL database.

This project demonstrates:

* File I/O with CSV files
* Data deduplication and normalization
* Input validation and error handling
* Argument-based program flow

## Project Structure

```
Challenge-05/
├── src/
│   └── split_data.py         # Main program logic
├── doc/
│   └── 2015.csv              # CSV file containing contest data
└── README.md                 # Project documentation
```

## How the Program Works

1. The program loads contest data from a CSV file passed as a command-line argument.
2. It validates the file exists, is not empty, and contains all required columns.
3. It deduplicates institutions by (Institution Name, City, State/Province, Country) and assigns each a unique ID.
4. It writes two output CSV files named after the input file:
   * `Institutions_YYYY.csv` — one row per unique institution
   * `Teams_YYYY.csv` — one row per team, linked to its institution by ID

## How to Run

### Requirements

* Python 3.10 or higher
* No third-party libraries required (uses Python's standard library only)

### Steps

1. Clone the repository from GitHub:

```bash
git clone https://github.com/andriastheI/Challenge-05.git
```

2. Navigate into the project directory:

```bash
cd Challenge-05
```

3. Ensure your contest CSV file is located inside the `doc/` folder.

4. Run the program from the terminal:

```bash
python src/split_data.py doc/2015.csv
```

Running it with a different year's file works the same way:

```bash
python src/split_data.py doc/2016.csv   # produces Institutions_2016.csv, Teams_2016.csv
python src/split_data.py doc/2017.csv   # produces Institutions_2017.csv, Teams_2017.csv
```

### Sample Output

```
OK: 'doc/2015.csv' passed all validation checks.
Loaded 9772 team(s) from 'doc/2015.csv'.
Found 1685 unique institution(s) across 9772 team(s).
Wrote 1685 institution(s) to 'Institutions_2015.csv'.
Wrote 9772 team(s) to 'Teams_2015.csv'.

Done! Output files are ready: Institutions_2015.csv, Teams_2015.csv
```

## Input File Format

The input CSV must have the following columns (in any order):

| Column         | Description                              |
|----------------|------------------------------------------|
| Institution    | Name of the school or university         |
| Team Number    | Unique registration number for the team  |
| City           | City where the institution is located    |
| State/Province | State or province (may be empty)         |
| Country        | Country where the institution is located |
| Advisor        | Faculty advisor for the team             |
| Problem        | Problem chosen by the team (A, B, C, D)  |
| Ranking        | Final ranking designation                |

> The script handles files saved with a UTF-8 BOM (common when exported from Excel) automatically.

## Output File Format

### Institutions_YYYY.csv

Contains one row per unique institution, deduplicated by
(Institution Name, City, State/Province, Country).

| Column           | Description                      |
|------------------|----------------------------------|
| Institution ID   | Auto-generated unique identifier |
| Institution Name | Name of the school or university |
| City             | City                             |
| State/Province   | State or province                |
| Country          | Country                          |

### Teams_YYYY.csv

Contains one row per team, with a foreign key linking back to the institution.

| Column         | Description                                   |
|----------------|-----------------------------------------------|
| Team Number    | Unique registration number                    |
| Advisor        | Faculty advisor                               |
| Problem        | Problem chosen (A, B, C, or D)                |
| Ranking        | Final ranking designation                     |
| Institution ID | Foreign key referencing Institutions_YYYY.csv |

## Validation and Error Messages

The script checks for the following before processing:

| Situation                    | Error Message                                               |
|------------------------------|-------------------------------------------------------------|
| File not found               | `ERROR: 'file.csv' not found. Make sure the file is in ...` |
| File is empty                | `ERROR: 'file.csv' is empty.`                               |
| Missing required columns     | `ERROR: 'file.csv' is missing expected column(s): ...`      |
| File has no data rows        | `ERROR: 'file.csv' has a header but no data rows.`          |
| Output file is open in Excel | `ERROR: Permission denied when writing '...'.`              |
| File cannot be decoded       | `ERROR: Could not decode 'file.csv'. Try saving as UTF-8.'` |

## Help

To see usage instructions directly from the command line:

```bash
python src/split_data.py --help
```

## Author

Andrias Zelele

Computer Science Student

## Notes

* Institution IDs are auto-generated starting from 1
* Institutions are deduplicated by name, city, state, and country combined
* Input validation prevents the program from running on malformed or missing files
* Designed for academic and educational use

## Purpose

This project is intended for academic and educational purposes only.
