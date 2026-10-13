"""Command-line interface for the Student Record Management System."""

import argparse
import sys

from student_records import FIELDNAMES, StudentRecordError, StudentRecordManager


def display_students(records):
    """Print records in a readable table without requiring third-party packages."""
    if not records:
        print("\nNo student records found.")
        return

    headers = ["ID", "Name", "Course", "Semester", "Marks"]
    keys = FIELDNAMES
    rows = [[str(record[key]) for key in keys] for record in records]
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]
    line = "-+-".join("-" * width for width in widths)
    print()
    print(" | ".join(headers[index].ljust(widths[index]) for index in range(len(headers))))
    print(line)
    for row in rows:
        print(" | ".join(row[index].ljust(widths[index]) for index in range(len(headers))))
    print(f"\nTotal records: {len(records)}")


def prompt_required(label):
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value
        print(f"{label} cannot be empty. Please try again.")


def add_student(manager):
    print("\n--- Add Student ---")
    try:
        record = manager.add_student(
            prompt_required("Student ID"),
            prompt_required("Full name"),
            prompt_required("Course"),
            prompt_required("Semester"),
            prompt_required("Marks (0-100)"),
        )
        print(f"Student '{record['name']}' added successfully.")
    except StudentRecordError as error:
        print(f"Error: {error}")


def update_student(manager):
    print("\n--- Update Student ---")
    student_id = prompt_required("Enter student ID")
    current = manager.get_student(student_id)
    if current is None:
        print("Student not found.")
        return

    print("Press Enter to keep the current value.")
    print(f"Name [{current['name']}]")
    name = input("> ").strip()
    print(f"Course [{current['course']}]")
    course = input("> ").strip()
    print(f"Semester [{current['semester']}]")
    semester = input("> ").strip()
    print(f"Marks [{current['marks']}]")
    marks = input("> ").strip()

    changes = {}
    if name:
        changes["name"] = name
    if course:
        changes["course"] = course
    if semester:
        changes["semester"] = semester
    if marks:
        changes["marks"] = marks

    if not changes:
        print("No changes made.")
        return
    try:
        updated = manager.update_student(student_id, **changes)
        if updated:
            print(f"Student '{updated['student_id']}' updated successfully.")
        else:
            print("Student not found.")
    except StudentRecordError as error:
        print(f"Error: {error}")


def delete_student(manager):
    print("\n--- Delete Student ---")
    student_id = prompt_required("Enter student ID")
    record = manager.get_student(student_id)
    if record is None:
        print("Student not found.")
        return
    confirmation = input(
        f"Delete {record['name']} (ID: {record['student_id']})? Type yes to confirm: "
    ).strip().casefold()
    if confirmation != "yes":
        print("Deletion cancelled.")
        return
    try:
        if manager.delete_student(student_id):
            print("Student deleted successfully.")
        else:
            print("Student not found.")
    except StudentRecordError as error:
        print(f"Error: {error}")


def search_students(manager):
    query = input("\nEnter ID, name, course, or semester to search: ").strip()
    display_students(manager.search_students(query))


def sort_students(manager):
    print("\nSort by: 1. ID  2. Name  3. Course  4. Semester  5. Marks")
    choices = {
        "1": "student_id",
        "2": "name",
        "3": "course",
        "4": "semester",
        "5": "marks",
    }
    choice = input("Choose a field: ").strip()
    if choice not in choices:
        print("Invalid sort choice.")
        return
    direction = input("Order (A for ascending, D for descending) [A]: ").strip().casefold()
    if direction not in ("", "a", "d"):
        print("Invalid order. Use A or D.")
        return
    try:
        display_students(manager.sort_students(
            by=choices[choice], descending=(direction == "d")
        ))
    except StudentRecordError as error:
        print(f"Error: {error}")


def show_menu():
    print(
        "\n========== STUDENT RECORD MANAGEMENT ==========\n"
        "1. Add student\n"
        "2. View all students\n"
        "3. Search students\n"
        "4. Update student\n"
        "5. Delete student\n"
        "6. Sort students\n"
        "0. Exit\n"
        "================================================"
    )


def run_app(data_file="data/students.csv"):
    try:
        manager = StudentRecordManager(data_file)
    except StudentRecordError as error:
        print(f"Could not start the application: {error}")
        return 1

    actions = {
        "1": lambda: add_student(manager),
        "2": lambda: display_students(manager.list_students()),
        "3": lambda: search_students(manager),
        "4": lambda: update_student(manager),
        "5": lambda: delete_student(manager),
        "6": lambda: sort_students(manager),
    }

    while True:
        show_menu()
        choice = input("Enter your choice: ").strip()
        if choice == "0":
            print("Thank you for using Student Record Management System.")
            return 0
        action = actions.get(choice)
        if action is None:
            print("Invalid choice. Please select 0 to 6.")
            continue
        try:
            action()
        except (StudentRecordError, OSError) as error:
            print(f"Error: {error}")


def main():
    parser = argparse.ArgumentParser(
        description="Beginner-friendly Student Record Management System"
    )
    parser.add_argument(
        "--data",
        default="data/students.csv",
        help="CSV file used to store records (default: data/students.csv)",
    )
    args = parser.parse_args()
    try:
        return run_app(args.data)
    except (EOFError, KeyboardInterrupt):
        print("\nApplication closed.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
