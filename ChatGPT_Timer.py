import sys
import json
from PyQt5.QtWidgets import (
  QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QListWidget, QMessageBox, QFileDialog
)
from PyQt5.QtCore import QTimer


class TimerApp(QWidget):
  def __init__(self):
    super().__init__()
    self.setWindowTitle("타이머 프로그램")
    self.setGeometry(100, 100, 400, 400)

    self.timers = []  # 타이머 리스트
    self.active_timer_index = None  # 현재 실행 중인 타이머의 인덱스
    self.total_seconds = 0  # 모든 타이머의 총 시간
    self.timer_instance = QTimer()  # 카운트다운을 제어하는 QTimer
    self.timer_instance.timeout.connect(self.update_active_timer)

    # 자동 저장 타이머
    self.auto_save_timer = QTimer()
    self.auto_save_timer.timeout.connect(self.auto_save_latest_timer)
    self.auto_save_timer.start(10000)  # 10초마다 실행

    self.init_ui()

  def init_ui(self):
    # 레이아웃 설정
    self.layout = QVBoxLayout()
    self.setLayout(self.layout)

    # 타이머 리스트
    self.timer_list = QListWidget()
    self.layout.addWidget(self.timer_list)

    # 타이머 추가 UI
    add_timer_layout = QHBoxLayout()
    self.timer_name_input = QLineEdit()
    self.timer_name_input.setPlaceholderText("타이머 이름")
    self.timer_time_input = QLineEdit()
    self.timer_time_input.setPlaceholderText("시간 (HH:MM)")
    add_timer_button = QPushButton("타이머 추가")
    add_timer_button.clicked.connect(self.add_timer)
    add_timer_layout.addWidget(self.timer_name_input)
    add_timer_layout.addWidget(self.timer_time_input)
    add_timer_layout.addWidget(add_timer_button)
    self.layout.addLayout(add_timer_layout)

    # 타이머 조작 버튼
    button_layout = QHBoxLayout()
    self.start_button = QPushButton("시작")
    self.start_button.clicked.connect(self.start_timer)
    self.stop_button = QPushButton("정지")
    self.stop_button.clicked.connect(self.stop_timer)
    save_button = QPushButton("저장")  # 저장 버튼 추가
    save_button.clicked.connect(self.save_timers_to_file)
    load_button = QPushButton("불러오기")  # 불러오기 버튼 추가
    load_button.clicked.connect(self.load_timers_from_file)
    button_layout.addWidget(self.start_button)
    button_layout.addWidget(self.stop_button)
    button_layout.addWidget(save_button)
    button_layout.addWidget(load_button)
    self.layout.addLayout(button_layout)

    # 타이머 이동, 삭제, 전체 삭제 버튼
    edit_button_layout = QHBoxLayout()
    move_up_button = QPushButton("위로 이동")
    move_up_button.clicked.connect(self.move_timer_up)
    move_down_button = QPushButton("아래로 이동")
    move_down_button.clicked.connect(self.move_timer_down)
    delete_button = QPushButton("삭제")
    delete_button.clicked.connect(self.delete_timer)
    clear_all_button = QPushButton("전체 삭제")
    clear_all_button.clicked.connect(self.clear_all_timers)
    edit_button_layout.addWidget(move_up_button)
    edit_button_layout.addWidget(move_down_button)
    edit_button_layout.addWidget(delete_button)
    edit_button_layout.addWidget(clear_all_button)
    self.layout.addLayout(edit_button_layout)

    # 메시지 레이블
    self.message_label = QLabel("")
    self.layout.addWidget(self.message_label)

  def add_timer(self):
    name = self.timer_name_input.text().strip()
    time_input = self.timer_time_input.text().strip()

    if not name or not time_input:
      self.show_message("타이머 이름과 시간을 입력하세요.", "error")
      return

    try:
      hours, minutes = map(int, time_input.split(":"))
      total_seconds = hours * 3600 + minutes * 60
    except ValueError:
      self.show_message("시간 형식이 올바르지 않습니다. (HH:MM)", "error")
      return

    if total_seconds <= 0:
      self.show_message("시간이 0인 타이머는 추가할 수 없습니다.", "error")
      return

    if self.total_seconds + total_seconds > 24 * 3600:
      self.show_message("타이머의 총 시간이 24시간을 초과할 수 없습니다.", "error")
      return

    timer = {"name": name, "time": total_seconds, "remaining": total_seconds, "active": False}
    self.timers.append(timer)
    self.total_seconds += total_seconds
    self.update_timer_list()
    self.show_message(f"'{name}' 타이머가 추가되었습니다.", "info")

  def start_timer(self):
    selected_index = self.timer_list.currentRow()
    if selected_index == -1:
      self.show_message("시작할 타이머를 선택하세요.", "error")
      return

    if self.active_timer_index is not None and self.active_timer_index != selected_index:
      self.show_message("한 번에 하나의 타이머만 실행할 수 있습니다.", "error")
      return

    timer = self.timers[selected_index]
    if timer["active"]:
      self.show_message(f"'{timer['name']}' 타이머가 이미 실행 중입니다.", "error")
      return

    self.active_timer_index = selected_index
    timer["active"] = True
    self.timer_instance.start(1000)  # 1초마다 업데이트
    self.update_timer_list()
    self.show_message(f"'{timer['name']}' 타이머를 시작했습니다.", "info")

  def stop_timer(self):
    if self.active_timer_index is None:
      self.show_message("현재 실행 중인 타이머가 없습니다.", "error")
      return

    timer = self.timers[self.active_timer_index]
    timer["active"] = False
    self.active_timer_index = None
    self.timer_instance.stop()
    self.update_timer_list()
    self.show_message("타이머가 정지되었습니다.", "info")

  def move_timer_up(self):
    selected_index = self.timer_list.currentRow()
    if selected_index > 0:
      # 타이머 순서 변경
      self.timers[selected_index], self.timers[selected_index - 1] = (
        self.timers[selected_index - 1],
        self.timers[selected_index],
      )
      # 실행 중인 타이머의 인덱스 업데이트
      if self.active_timer_index == selected_index:
        self.active_timer_index = selected_index - 1
      elif self.active_timer_index == selected_index - 1:
        self.active_timer_index = selected_index
      self.update_timer_list()
      self.timer_list.setCurrentRow(selected_index - 1)

  def move_timer_down(self):
    selected_index = self.timer_list.currentRow()
    if selected_index < len(self.timers) - 1:
      # 타이머 순서 변경
      self.timers[selected_index], self.timers[selected_index + 1] = (
        self.timers[selected_index + 1],
        self.timers[selected_index],
      )
      # 실행 중인 타이머의 인덱스 업데이트
      if self.active_timer_index == selected_index:
        self.active_timer_index = selected_index + 1
      elif self.active_timer_index == selected_index + 1:
        self.active_timer_index = selected_index
      self.update_timer_list()
      self.timer_list.setCurrentRow(selected_index + 1)

  def delete_timer(self):
    selected_index = self.timer_list.currentRow()
    if selected_index == -1:
      self.show_message("삭제할 타이머를 선택하세요.", "error")
      return

    deleted_timer = self.timers.pop(selected_index)
    self.total_seconds -= deleted_timer["time"]
    self.update_timer_list()
    self.show_message(f"'{deleted_timer['name']}' 타이머가 삭제되었습니다.", "info")

  def clear_all_timers(self):
    self.timers = []
    self.total_seconds = 0
    self.active_timer_index = None
    self.timer_instance.stop()
    self.update_timer_list()
    self.show_message("모든 타이머가 삭제되었습니다.", "info")

  def save_timers_to_file(self):
    file_path, _ = QFileDialog.getSaveFileName(self, "타이머 저장", "", "JSON Files (*.json)")
    if file_path:
      with open(file_path, "w") as f:
        json.dump(self.timers, f)
      self.show_message("타이머가 저장되었습니다.", "info")

  def load_timers_from_file(self):
    file_path, _ = QFileDialog.getOpenFileName(self, "타이머 불러오기", "", "JSON Files (*.json)")
    if file_path:
      with open(file_path, "r") as f:
        self.timers = json.load(f)

      # 모든 타이머를 정지 상태로 변경
      for timer in self.timers:
        timer["active"] = False
        timer["remaining"] = timer["time"]  # 초기화된 상태로 설정

      self.total_seconds = sum(timer["time"] for timer in self.timers)
      self.active_timer_index = None
      self.timer_instance.stop()
      self.update_timer_list()
      self.show_message("타이머가 불러와졌습니다. 모든 타이머는 정지 상태로 초기화되었습니다.", "info")

  def auto_save_latest_timer(self):
    with open("Latest Timer.json", "w") as f:
      json.dump(self.timers, f)

  def update_active_timer(self):
    if self.active_timer_index is not None:
      timer = self.timers[self.active_timer_index]
      timer["remaining"] -= 1
      if timer["remaining"] <= 0:
        self.show_message(f"'{timer['name']}' 타이머가 완료되었습니다.", "info")
        self.show_popup(f"'{timer['name']}' 타이머가 완료되었습니다.")
        timer["active"] = False
        self.active_timer_index = None
        self.timer_instance.stop()
    self.update_timer_list()

  def update_timer_list(self):
    selected_index = self.timer_list.currentRow()  # 선택 상태 유지
    self.timer_list.clear()
    for timer in self.timers:
      remaining_minutes, remaining_seconds = divmod(timer["remaining"], 60)
      remaining_hours, remaining_minutes = divmod(remaining_minutes, 60)
      status = "실행 중" if timer["active"] else "대기 중"
      self.timer_list.addItem(
        f"{timer['name']} - {remaining_hours:02}:{remaining_minutes:02}:{remaining_seconds:02} ({status})"
      )
    if selected_index != -1:
      self.timer_list.setCurrentRow(selected_index)

  def show_message(self, text, message_type="info"):
    color = "blue" if message_type == "info" else "red"
    self.message_label.setStyleSheet(f"color: {color}")
    self.message_label.setText(text)

  def show_popup(self, message):
    QMessageBox.information(self, "타이머 완료", message)


if __name__ == "__main__":
  app = QApplication(sys.argv)
  window = TimerApp()
  window.show()
  sys.exit(app.exec_())
