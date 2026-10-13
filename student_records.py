"""Core logic for the beginner-friendly Student Record Management System.

The project uses only Python's standard library. Records are stored in a CSV file.
"""

import csv
import os
import tempfile
from pathlib import Path

FIELDNAMES = ["student_id", "name", "course", "semester", "marks"]


class StudentRecordError(Exception):
    """Raised when a student record cannot be created or updated safely."""


class StudentRecordManager:
    """Create, read, update, delete, search, and sort student records."""

    def __init__(self, data_file="data/students.csv"):
        self.data_file = Path(data_file)
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.data_file.exists():
            self._write_all([])

    @staticmethod
    def _clean_text(value, field_name):
        cleaned = str(value).strip()
        if not cleaned:
            raise StudentRecordError(f"{field_name} cannot be empty.")
        return cleaned

    @staticmethod
    def _clean_marks(value):
        try:
            marks = float(value)
        except (TypeError, ValueError):
            raise StudentRecordError("Marks must be a number between 0 and 100.") from None
        if not 0 <= marks <= 100:
            raise StudentRecordError("Marks must be between 0 and 100.")
        # Keep whole-number marks tidy in the CSV, without losing decimal marks.
        return str(int(marks)) if marks.is_integer() else f"{marks:g}"

    def _normalise_record(self, record):
        student_id = self._clean_text(record.get("student_id", ""), "Student ID")
        name = self._clean_text(record.get("name", ""), "Name")
        course = self._clean_text(record.get("course", ""), "Course")
        semester = self._clean_text(record.get("semester", ""), "Semester")
        marks = self._clean_marks(record.get("marks", ""))
        return {
            "student_id": student_id,
            "name": name,
            "course": course,
            "semester": semester,
            "marks": marks,
        }

    def _read_all(self):
        """Read all records; report malformed files clearly instead of silently losing data."""
        try:
            with self.data_file.open("r", newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                if reader.fieldnames is None:
                    return []
                if reader.fieldnames != FIELDNAMES:
                    raise StudentRecordError(
                        "The CSV file has an unexpected format. "
                        "Restore the required header: " + ", ".join(FIELDNAMES)
                    )
                records = []
                seen_ids = set()
                for line_number, row in enumerate(reader, start=2):
                    if not row or all(value is None or not value.strip() for value in row.values()):
                        continue
                    try:
                        record = self._normalise_record(row)
                    except StudentRecordError as error:
                        raise StudentRecordError(
                            f"Invalid record on CSV line {line_number}: {error}"
                        ) from error
                    key = record["student_id"].casefold()
                    if key in seen_ids:
                        raise StudentRecordError(
                            f"Duplicate student ID on CSV line {line_number}: "
                            f"{record['student_id']}"
                        )
                    seen_ids.add(key)
                    records.append(record)
                return records
        except UnicodeDecodeError as error:
            raise StudentRecordError("The CSV file is not valid UTF-8 text.") from error
        except csv.Error as error:
            raise StudentRecordError(f"Could not read the CSV file: {error}") from error

    def _write_all(self, records):
        """Write atomically so an interrupted save is less likely to corrupt the CSV."""
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        temp_name = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                newline="",
                encoding="utf-8",
                dir=self.data_file.parent,
                delete=False,
            ) as file:
                temp_name = file.name
                writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
                writer.writeheader()
                writer.writerows(records)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temp_name, self.data_file)
        except OSError as error:
            if temp_name and os.path.exists(temp_name):
                try:
                    os.remove(temp_name)
                except OSError:
                    pass
            raise StudentRecordError(f"Could not save records: {error}") from error

    def add_student(self, student_id, name, course, semester, marks):
        record = self._normalise_record({
            "student_id": student_id,
            "name": name,
            "course": course,
            "semester": semester,
            "marks": marks,
        })
        records = self._read_all()
        if any(item["student_id"].casefold() == record["student_id"].casefold()
               for item in records):
            raise StudentRecordError(f"Student ID '{record['student_id']}' already exists.")
        records.append(record)
        self._write_all(records)
        return record.copy()

    def list_students(self):
        """Return a new list so callers cannot mutate internal state."""
        return [record.copy() for record in self._read_all()]

    def get_student(self, student_id):
        wanted = str(student_id).strip().casefold()
        for record in self._read_all():
            if record["student_id"].casefold() == wanted:
                return record.copy()
        return None

    def update_student(self, student_id, **changes):
        allowed = {"name", "course", "semester", "marks"}
        unknown = set(changes) - allowed
        if unknown:
            raise StudentRecordError("Unsupported field(s): " + ", ".join(sorted(unknown)))
        records = self._read_all()
        for index, record in enumerate(records):
            if record["student_id"].casefold() == str(student_id).strip().casefold():
                updated = record.copy()
                updated.update(changes)
                updated = self._normalise_record(updated)
                records[index] = updated
                self._write_all(records)
                return updated.copy()
        return None

    def delete_student(self, student_id):
        wanted = str(student_id).strip().casefold()
        records = self._read_all()
        remaining = [record for record in records
                     if record["student_id"].casefold() != wanted]
        if len(remaining) == len(records):
            return False
        self._write_all(remaining)
        return True

    def search_students(self, query):
        query = str(query).strip().casefold()
        if not query:
            return []
        return [
            record.copy()
            for record in self._read_all()
            if any(query in record[field].casefold()
                   for field in ("student_id", "name", "course", "semester"))
        ]

    def sort_students(self, by="name", descending=False):
        allowed = {"student_id", "name", "course", "semester", "marks"}
        if by not in allowed:
            raise StudentRecordError(
                "Sort field must be one of: " + ", ".join(sorted(allowed))
            )
        records = self._read_all()
        if by == "marks":
            records.sort(key=lambda item: float(item["marks"]), reverse=descending)
        else:
            records.sort(key=lambda item: item[by].casefold(), reverse=descending)
        return [record.copy() for record in records]
