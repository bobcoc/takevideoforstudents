import tkinter as tk
from tkinter import Label, Button, Checkbutton, IntVar
from PIL import Image, ImageTk
import cv2
import openpyxl
import subprocess
import os
import signal
import threading

def load_students_info(excel_path):
    """从 Excel 文件读取学生信息"""
    workbook = openpyxl.load_workbook(excel_path)
    sheet = workbook.active
    students_info = []
    for row in sheet.iter_rows(min_row=2):
        exam_id = row[0].value
        name = row[1].value
        if exam_id and name:
            students_info.append((exam_id, name))
    return students_info

class CameraApp:
    def __init__(self, master, students_info):
        self.master = master
        self.students_info = students_info
        self.current_student_index = 0
        self.ffmpeg_process = None
        self.mode_var = IntVar()
        self.master.title("学生录像系统")
        self.master.geometry("800x600")

        self.vid = cv2.VideoCapture(0)
        self.vid.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        self.canvas = tk.Canvas(master, width=800, height=500)
        self.canvas.pack()
        
        self.label = Label(master, text="")
        self.label.pack()

        self.btn_snapshot = Button(master, text="开始/停止录像", command=self.toggle_recording)
        self.btn_snapshot.pack()

        self.btn_previous = Button(master, text="上一个学生", command=self.previous_student)
        self.btn_previous.pack()

        self.btn_next = Button(master, text="下一个学生", command=self.next_student)
        self.btn_next.pack()

        self.chk_mode = Checkbutton(master, text="录像模式", variable=self.mode_var, command=self.toggle_mode)
        self.chk_mode.pack()

        self.update_student_info()
        self.update()

    def toggle_mode(self):
        """根据复选框切换模式"""
        if self.ffmpeg_process:
            self.stop_recording()

    def toggle_recording(self):
        """根据模式开始或停止录像"""
        if self.mode_var.get() == 1:  # 录像模式
            if self.ffmpeg_process:
                self.stop_recording()
                self.next_student()
            else:
                self.start_recording()
        else:  # 拍照模式
            self.take_snapshot()
            self.next_student()

    def start_recording(self):
        """开始录像"""
        exam_id, name = self.students_info[self.current_student_index]
        video_name = f"{exam_id}_{name}.mp4"
        
        command = [
            "ffmpeg",
            "-f", "avfoundation",
            "-framerate", "30",
            "-video_size", "1280x720",
            "-i", "0:0",  # 使用默认视频和音频设备
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-c:a", "aac",
            "-movflags", "+faststart",
            "-y",
            video_name
        ]
        
        self.ffmpeg_process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Recording started for {name} ({exam_id}).")

    def stop_recording(self):
        """停止录像并保存文件"""
        if self.ffmpeg_process:
            self.ffmpeg_process.send_signal(signal.SIGINT)
            try:
                self.ffmpeg_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.ffmpeg_process.kill()
                self.ffmpeg_process.wait()
            self.ffmpeg_process = None
            exam_id, name = self.students_info[self.current_student_index]
            print(f"Recording stopped and saved for {name} ({exam_id}).")

    def take_snapshot(self):
        """拍照功能"""
        ret, frame = self.vid.read()
        if ret:
            exam_id, name = self.students_info[self.current_student_index]
            cv2.imwrite(f"{exam_id}_{name}.png", frame)
            print(f"Photo saved as {exam_id}_{name}.png")

    def next_student(self):
        """切换到下一个学生"""
        if self.current_student_index < len(self.students_info) - 1:
            if self.ffmpeg_process:
                self.stop_recording()
            self.current_student_index += 1
            self.update_student_info()

    def previous_student(self):
        """切换到上一个学生"""
        if self.current_student_index > 0:
            if self.ffmpeg_process:
                self.stop_recording()
            self.current_student_index -= 1
            self.update_student_info()

    def update_student_info(self):
        """更新当前学生信息"""
        exam_id, name = self.students_info[self.current_student_index]
        self.label.config(text=f"当前学生：{name} ({exam_id})")

    def update(self):
        """更新画布上的图像"""
        ret, frame = self.vid.read()
        if ret:
            frame_resized = cv2.resize(frame, (800, 500))  # Resize the frame
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
        self.master.after(10, self.update)

    def cleanup(self):
        """清理资源"""
        if self.ffmpeg_process:
            self.stop_recording()
        if self.vid.isOpened():
            self.vid.release()
        self.master.quit()

if __name__ == "__main__":
    root = tk.Tk()
    students_info = load_students_info("mt.xlsx")
    app = CameraApp(root, students_info)
    root.protocol("WM_DELETE_WINDOW", app.cleanup)
    root.mainloop()
