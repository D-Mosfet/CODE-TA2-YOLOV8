from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUiType
import sys
import sqlite3
from datetime import date, datetime
import cv2
import os
import numpy as np
from ultralytics import YOLO  # Pastikan modul ultralytics sudah diinstal

ui, _ = loadUiType('face-reco.ui')

# Kamus untuk memetakan nama ke NIM
nim_dict = {
    "Dhery Akbar": "1102200018",
    "Fadeta Ilhan": "1102200098",
    "Handi Achmad": "1102200088",
    "Iqbal Farissi": "1102200099",
    "Akbar Qodri": "1102200033",
    "Eka Sari Oktarina": "1102200022"
}

class MainApp(QMainWindow, ui):
    def __init__(self):
        super(MainApp, self).__init__()
        self.setupUi(self)
        self.tabWidget.setCurrentIndex(0)
        self.LOGINBUTTON.clicked.connect(self.login)
        self.LOGOUTBUTTON.clicked.connect(self.logout)
        self.CLOSEBUTTON.clicked.connect(self.close_window)
        self.ATTLINK1.clicked.connect(self.show_attendance_entry_form)
        self.REPORTSLINK1.clicked.connect(self.show_reports_form)
        self.ATTENDANCEBACK.clicked.connect(self.show_mainform)
        self.REPORTSBACK.clicked.connect(self.show_mainform)
        self.RECORD.clicked.connect(self.record_attendance)
        self.dateEdit.setDate(date.today())
        self.dateEdit.dateChanged.connect(self.show_selected_date_reports)
        self.tabWidget.setStyleSheet("QTabWidget::pane{border:0;}")

        try:
            con = sqlite3.connect("face-reco.db")
            con.execute(
                "CREATE TABLE IF NOT EXISTS attendance(nim TEXT PRIMARY KEY, name TEXT, attendancedate TEXT, attendance_time TEXT)"
            )
            con.commit()
            print("Table created successfully")
        except Exception as e:
            print(f"Error in database: {e}")

        self.update_database()

    def update_database(self):
        con = sqlite3.connect("face-reco.db")
        cursor = con.cursor()
        cursor.execute("PRAGMA table_info(attendance)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        if "attendance_time" not in column_names:
            cursor.execute("ALTER TABLE attendance ADD COLUMN attendance_time TEXT")
            con.commit()
            print("Added 'attendance_time' column to the attendance table.")
        con.close()

    ### LOGIN PROCESS ###
    def login(self):
        pw = self.PASSWORD.text()
        if pw == "admin123":
            self.PASSWORD.setText("")
            self.LOGININFO.setText("")
            self.tabWidget.setCurrentIndex(1)
        else:
            self.LOGININFO.setText("Invalid Password..")
            self.PASSWORD.setText("")

    ### LOG OUT PROCESS ###
    def logout(self):
        self.tabWidget.setCurrentIndex(0)

    ### CLOSE WINDOW PROCESS ###
    def close_window(self):
        self.close()

    ### SHOW MAIN FORM ###
    def show_mainform(self):
        self.tabWidget.setCurrentIndex(1)

    ### SHOW ATTENDANCE ENTRY FORM ###
    def show_attendance_entry_form(self):
        self.tabWidget.setCurrentIndex(2)

    ### SHOW REPORTS FORM ###
    def show_reports_form(self):
        self.tabWidget.setCurrentIndex(3)
        self.REPORTS.setRowCount(0)
        self.REPORTS.clear()
        con = sqlite3.connect("face-reco.db")
        cursor = con.execute("SELECT row_number() OVER (ORDER BY nim) AS NO, name, nim, attendancedate, attendance_time FROM attendance")
        result = cursor.fetchall()
        r = 0
        c = 0
        for row_number, row_data in enumerate(result):
            r += 1
            c = 0
            for column_number, data in enumerate(row_data):
                c += 1
        self.REPORTS.setColumnCount(c)

        for row_number, row_data in enumerate(result):
            self.REPORTS.insertRow(row_number)
            for column_number, data in enumerate(row_data):
                self.REPORTS.setItem(row_number, column_number, QTableWidgetItem(str(data)))

        self.REPORTS.setHorizontalHeaderLabels(['NO', 'Name', 'NIM', 'Date', 'Time'])
        self.REPORTS.setColumnWidth(0, 10)
        self.REPORTS.setColumnWidth(1, 180)
        self.REPORTS.setColumnWidth(2, 100)
        self.REPORTS.setColumnWidth(3, 100)
        self.REPORTS.setColumnWidth(4, 100)
        self.REPORTS.verticalHeader().setVisible(False)

    ### SHOW SELECTED DATE REPORTS ###
    def show_selected_date_reports(self):
        self.REPORTS.setRowCount(0)
        self.REPORTS.clear()
        con = sqlite3.connect("face-reco.db")
        cursor = con.execute(
            "SELECT row_number() OVER (ORDER BY nim) AS NO, name, nim, attendancedate, attendance_time FROM attendance WHERE attendancedate = '" + str((self.dateEdit.date()).toPyDate()) + "'")
        result = cursor.fetchall()
        r = 0
        c = 0
        for row_number, row_data in enumerate(result):
            r += 1
            c = 0
            for column_number, data in enumerate(row_data):
                c += 1
        self.REPORTS.setColumnCount(c)

        for row_number, row_data in enumerate(result):
            self.REPORTS.insertRow(row_number)
            for column_number, data in enumerate(row_data):
                self.REPORTS.setItem(row_number, column_number, QTableWidgetItem(str(data)))

        self.REPORTS.setHorizontalHeaderLabels(['NO', 'Name', 'NIM', 'Date', 'Time'])
        self.REPORTS.setColumnWidth(0, 10)
        self.REPORTS.setColumnWidth(1, 180)
        self.REPORTS.setColumnWidth(2, 70)
        self.REPORTS.setColumnWidth(3, 70)
        self.REPORTS.setColumnWidth(4, 70)
        self.REPORTS.verticalHeader().setVisible(False)


    ### RECORD ATTENDANCE ###
    def record_attendance(self):
        self.currentprocess.setText("Process started.. Waiting..")

        # Hyperparameters
        confidence_threshold = 0.6  # Confidence threshold untuk deteksi

        # Inisialisasi YOLO model
        model = YOLO('D:/dataset8/runs/best.pt')  # Ganti dengan model YOLOv8 Anda

        # Class names sesuai model Anda
        classNames = [
            "Akbar Qodri",
            "Dhery Akbar",
            "Eka Sari Oktarina",
            "Fadeta Ilhan",
            "Fake",
            "Handi Achmad",
            "Iqbal Farissi",
        ]

        # Inisialisasi webcam
        cap = cv2.VideoCapture(2) # Ganti dengan 1 atau 2 jika ada beberapa kamera

        # Mengatur resolusi webcam
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

        if not cap.isOpened():
            print("Error: Tidak dapat membuka webcam.")
            return

        attendance_successful = False  # Flag untuk memastikan absensi berhasil

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Tidak dapat membaca frame dari webcam.")
                break

            # Deteksi wajah menggunakan model YOLOv8
            results = model(frame)

            # Proses hasil deteksi dan tampilkan di frame
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    confidence = box.conf[0]
                    class_id = int(box.cls[0])

                    # Jika nilai confidence di bawah threshold, abaikan deteksi ini
                    if confidence < confidence_threshold:
                        continue  # Abaikan deteksi ini dan lanjutkan ke berikutnya

                    label = classNames[class_id] if class_id < len(classNames) else "Unknown"

                    # Gambarkan bounding box dan informasi di frame
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f'{label} {confidence:.2f}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9,
                                (0, 255, 0), 2)

                    # Daftarkan kehadiran di database jika bukan "Unknown" atau "Fake"
                    if label != "Unknown" and label != "Fake":
                        self.register_attendance(label)
                        attendance_successful = True  # Set flag menjadi True

            cv2.imshow("Face Recognition", frame)
            key = cv2.waitKey(10)
            if key == 27:  # Tekan ESC untuk keluar
                break

        cap.release()
        cv2.destroyAllWindows()

        # Tampilkan notifikasi jika absensi berhasil
        if attendance_successful:
            QMessageBox.information(self, "Attendance Recorded", "Attendance successfully recorded for detected individuals.")

    ### REGISTER ATTENDANCE ###
    def register_attendance(self, name):
        current_time = datetime.now().strftime("%H:%M:%S")  # Mendapatkan waktu saat ini dalam format HH:MM:SS
        current_date = str(date.today())  # Mendapatkan tanggal saat ini

        # Dapatkan NIM dari kamus nim_dict berdasarkan nama
        nim = nim_dict.get(name, "Unknown NIM")

        try:
            con = sqlite3.connect("face-reco.db")
            cursor = con.cursor()
            cursor.execute("SELECT nim FROM attendance WHERE nim=? AND attendancedate=?", (nim, current_date))
            result = cursor.fetchone()

            if result:
                # Jika ada catatan, perbarui dengan waktu terbaru
                cursor.execute("UPDATE attendance SET attendance_time=? WHERE nim=?", (current_time, nim))
                con.commit()
                print(f"Attendance updated for {name} at {current_time}.")  # Debugging output
            else:
                # Jika tidak ada catatan, buat catatan baru
                cursor.execute("INSERT INTO attendance (nim, name, attendancedate, attendance_time) VALUES (?, ?, ?, ?)",
                               (nim, name, current_date, current_time))
                con.commit()
                print(f"Attendance recorded for {name} with NIM {nim} at {current_time}.")  # Debugging output

            con.close()
        except Exception as e:
            print(f"Error in database: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    app.exec_()
