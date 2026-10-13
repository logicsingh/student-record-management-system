"""Automated tests for StudentRecordManager using only unittest."""

import csv
import tempfile
import unittest
from pathlib import Path

from student_records import StudentRecordError, StudentRecordManager


class StudentRecordManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_file = Path(self.temp_dir.name) / "students.csv"
        self.manager = StudentRecordManager(self.data_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def add_sample(self, student_id="S001", name="Aarav Sharma",
                   course="BSc Computer Science", semester="3", marks="82"):
        return self.manager.add_student(student_id, name, course, semester, marks)

    def test_new_file_has_csv_header(self):
        with self.data_file.open(newline="", encoding="utf-8") as file:
            self.assertEqual(
                next(csv.reader(file)),
                ["student_id", "name", "course", "semester", "marks"],
            )

    def test_add_and_list_student(self):
        self.add_sample()
        records = self.manager.list_students()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["name"], "Aarav Sharma")
        self.assertEqual(records[0]["marks"], "82")

    def test_duplicate_id_is_case_insensitive(self):
        self.add_sample("S001")
        with self.assertRaisesRegex(StudentRecordError, "already exists"):
            self.add_sample("s001", "Another Student")

    def test_required_fields_cannot_be_blank(self):
        with self.assertRaisesRegex(StudentRecordError, "Name cannot be empty"):
            self.add_sample(name="  ")

    def test_marks_must_be_between_zero_and_one_hundred(self):
        for marks in ("-1", "101", "not-a-number", ""):
            with self.subTest(marks=marks):
                with self.assertRaises(StudentRecordError):
                    self.add_sample(marks=marks)

    def test_decimal_marks_are_supported(self):
        record = self.add_sample(marks="82.5")
        self.assertEqual(record["marks"], "82.5")

    def test_search_matches_name_and_course_without_case_sensitivity(self):
        self.add_sample()
        self.add_sample("S002", "Mira Patel", "BCA", "2", "91")
        self.assertEqual(len(self.manager.search_students("AARAV")), 1)
        self.assertEqual(len(self.manager.search_students("bca")), 1)

    def test_update_student(self):
        self.add_sample()
        updated = self.manager.update_student("S001", name="Aarav S.", marks="90")
        self.assertEqual(updated["name"], "Aarav S.")
        self.assertEqual(updated["marks"], "90")
        self.assertIsNone(self.manager.update_student("missing", name="Nobody"))

    def test_invalid_update_does_not_change_saved_record(self):
        self.add_sample()
        with self.assertRaises(StudentRecordError):
            self.manager.update_student("S001", marks="200")
        self.assertEqual(self.manager.get_student("S001")["marks"], "82")

    def test_delete_student(self):
        self.add_sample()
        self.assertTrue(self.manager.delete_student("S001"))
        self.assertEqual(self.manager.list_students(), [])
        self.assertFalse(self.manager.delete_student("S001"))

    def test_sort_by_marks_numerically(self):
        self.add_sample("S001", "Aarav", "BSc CS", "3", "9")
        self.add_sample("S002", "Mira", "BSc CS", "3", "80")
        self.assertEqual(
            [row["student_id"] for row in self.manager.sort_students("marks")],
            ["S001", "S002"],
        )
        self.assertEqual(
            [row["student_id"] for row in self.manager.sort_students("marks", True)],
            ["S002", "S001"],
        )

    def test_data_persists_after_manager_restarts(self):
        self.add_sample()
        reopened = StudentRecordManager(self.data_file)
        self.assertEqual(reopened.get_student("S001")["name"], "Aarav Sharma")

    def test_name_with_comma_is_stored_correctly(self):
        self.add_sample(name="Sharma, Aarav")
        reopened = StudentRecordManager(self.data_file)
        self.assertEqual(reopened.get_student("S001")["name"], "Sharma, Aarav")

    def test_bad_csv_header_is_reported(self):
        self.data_file.write_text("wrong,header\\nvalue,other\\n", encoding="utf-8")
        with self.assertRaisesRegex(StudentRecordError, "unexpected format"):
            self.manager.list_students()


if __name__ == "__main__":
    unittest.main()
